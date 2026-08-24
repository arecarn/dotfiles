/**
 * Background process behind one monitor: spawn, line splitting, truncation, rate
 * limiting, exit handling.
 *
 * Deliberately free of pi API calls, so what a monitor emits can be checked by
 * reading this file alone. Everything session-shaped lives in registry.ts and
 * index.ts.
 */

import { type ChildProcess, spawn } from "node:child_process";

/**
 * Cap on the characters of one stdout line held in memory or put in an event.
 * Every cut it causes is marked in the event.
 */
const MAX_LINE_CHARS = 2000;
/** Events emitted per second before the excess is coalesced into one event. */
const MAX_EVENTS_PER_WINDOW = 10;
const RATE_WINDOW_MS = 1000;
/**
 * Trailing stderr kept for the exit event. stderr is diagnostics, never an
 * event, so only the tail that explains a failure is worth holding.
 */
const STDERR_TAIL_CHARS = 1000;

export type MonitorExit = {
	code: number | null;
	signal: NodeJS.Signals | null;
};

export type MonitorProcessSpec = {
	command: string;
	cwd: string;
};

export type MonitorProcessCallbacks = {
	/** One call per event: a stdout line, a suppression notice, or the exit notice. */
	onEvent: (text: string) => void;
	/** Called once, after the last event, unless kill() got there first. */
	onExit: (exit: MonitorExit) => void;
};

export type MonitorProcess = {
	/**
	 * Kill the process tree and stop emitting. Safe to call repeatedly, and after
	 * the process has already exited.
	 */
	kill: () => void;
};

/**
 * Start `spec.command` in `spec.cwd` and report its stdout as events.
 *
 * Each non-blank stdout line is one event, truncated to MAX_LINE_CHARS and rate
 * limited. A command that exits having emitted nothing still gets one event
 * naming its exit code, because a watch that died silently is otherwise
 * indistinguishable from one still waiting.
 */
export function startMonitorProcess(
	spec: MonitorProcessSpec,
	callbacks: MonitorProcessCallbacks,
): MonitorProcess {
	// The user's login shell, so a monitor command behaves as it would if typed;
	// Node falls back to /bin/sh (or ComSpec on Windows) when SHELL is unset. A
	// bash-only command under a shell like fish fails at parse time, which arrives
	// as the exit event rather than as silence.
	//
	// detached puts the shell in its own process group, which is what makes the
	// kill below reach the whole tree.
	const child = spawn(spec.command, {
		cwd: spec.cwd,
		shell: process.env.SHELL || true,
		detached: true,
		stdio: ["ignore", "pipe", "pipe"],
		windowsHide: true,
	});

	let stopped = false;
	let settled = false;
	let eventsEmitted = 0;
	let windowStart = Date.now();
	let eventsInWindow = 0;
	let suppressed = 0;
	let suppressionTimer: NodeJS.Timeout | undefined;
	let stdoutCarry = "";
	/** Characters the carry cap dropped from the front of the line being carried. */
	let stdoutCarryDropped = 0;
	let stderrTail = "";

	const emit = (text: string): void => {
		if (stopped) {
			return;
		}
		eventsEmitted += 1;
		callbacks.onEvent(text);
	};

	const clearSuppressionTimer = (): void => {
		if (suppressionTimer !== undefined) {
			clearTimeout(suppressionTimer);
			suppressionTimer = undefined;
		}
	};

	const flushSuppressed = (): void => {
		clearSuppressionTimer();
		if (suppressed === 0) {
			return;
		}
		const count = suppressed;
		suppressed = 0;
		emit(
			`${count} event${count === 1 ? "" : "s"} suppressed by the ${MAX_EVENTS_PER_WINDOW}/s rate limit`,
		);
	};

	// A runaway command must cost a bounded amount of context: past the per-window
	// allowance, lines are counted rather than emitted, and the count goes out as
	// one event. Callers pass finished event text; formatStdoutLine does the cutting.
	const emitLine = (text: string): void => {
		const now = Date.now();
		if (now - windowStart >= RATE_WINDOW_MS) {
			flushSuppressed();
			windowStart = now;
			eventsInWindow = 0;
		}
		if (eventsInWindow >= MAX_EVENTS_PER_WINDOW) {
			suppressed += 1;
			// Without this timer, a command that falls quiet after a burst would hold
			// its suppression notice until its next line or its exit.
			if (suppressionTimer === undefined) {
				suppressionTimer = setTimeout(
					flushSuppressed,
					RATE_WINDOW_MS - (now - windowStart),
				);
				suppressionTimer.unref();
			}
			return;
		}
		eventsInWindow += 1;
		emit(text);
	};

	child.stdout?.setEncoding("utf8");
	child.stdout?.on("data", (chunk: string) => {
		const lines = (stdoutCarry + chunk).split("\n");
		stdoutCarry = lines.pop() ?? "";
		for (const line of lines) {
			// Only the first completed line can carry dropped characters: they are the
			// front of the line the newline just ended.
			const dropped = stdoutCarryDropped;
			stdoutCarryDropped = 0;
			const event = formatStdoutLine(line, dropped);
			if (event !== "") {
				emitLine(event);
			}
		}
		// Cap the carry, keeping the newest characters. Truncating finished lines does
		// not cover this: a command that reports progress with \r and no newline (curl,
		// docker pull, npm) never finishes a line at all, so the carry would grow for
		// the life of the monitor. Progress output makes its newest end the useful one,
		// and what goes is counted so the event can still say the line was cut.
		if (stdoutCarry.length > MAX_LINE_CHARS) {
			stdoutCarryDropped += stdoutCarry.length - MAX_LINE_CHARS;
			stdoutCarry = stdoutCarry.slice(-MAX_LINE_CHARS);
		}
	});

	child.stderr?.setEncoding("utf8");
	child.stderr?.on("data", (chunk: string) => {
		stderrTail = (stderrTail + chunk).slice(-STDERR_TAIL_CHARS);
	});

	const finish = (code: number | null, signal: NodeJS.Signals | null): void => {
		if (settled || stopped) {
			return;
		}
		settled = true;
		const trailing = formatStdoutLine(stdoutCarry, stdoutCarryDropped);
		stdoutCarry = "";
		stdoutCarryDropped = 0;
		if (trailing !== "") {
			emitLine(trailing);
		}
		// After the last line, not before it: a trailing line the rate limit swallowed
		// has to be counted in the notice, and nothing flushes it later.
		flushSuppressed();
		if (eventsEmitted === 0) {
			const diagnosis =
				stderrTail.trim() === "" ? "" : `; last stderr: ${stderrTail.trim()}`;
			emit(
				`exited ${describeTermination(code, signal)} without producing output${diagnosis}`,
			);
		}
		callbacks.onExit({ code, signal });
	};

	// "close" rather than "exit": "exit" can fire before the stdout pipe has been
	// drained, which would report a command's last lines as no output at all.
	child.on("close", finish);
	child.on("error", (error) => {
		stderrTail = `${stderrTail}${error.message}\n`.slice(-STDERR_TAIL_CHARS);
		finish(null, null);
	});

	return {
		kill: () => {
			// stopped also suppresses onExit: the caller that killed the monitor has
			// already recorded its final state, and the process group's death signal
			// is not news.
			stopped = true;
			clearSuppressionTimer();
			killProcessTree(child);
		},
	};
}

/**
 * Event text for one logical stdout line, or "" for a line that is not an event.
 *
 * `raw` is what survived the carry cap and `dropped` is what that cap discarded
 * from the front of the same line. Either loss, or both on one line, is reported
 * as the span of the line that was kept, counted in characters as received: a
 * shortened line must never read as a complete one, and the span's own ends say
 * which end of the line survived. A blank line is no event, unless characters were
 * dropped from it, in which case it was not blank.
 */
function formatStdoutLine(raw: string, dropped: number): string {
	// A line the carry already cut is progress-style output, and its newest end is
	// what a reader wants: a stream of \r updates ends with the status that matters.
	// A line seen whole keeps its beginning instead, where a log line states what it
	// is. Without the first rule, a capped carry plus a final `done` in the next
	// chunk would cut that `done` off again.
	let kept = raw;
	if (raw.length > MAX_LINE_CHARS) {
		kept =
			dropped > 0 ? raw.slice(-MAX_LINE_CHARS) : raw.slice(0, MAX_LINE_CHARS);
	}
	const text = kept.trim();
	if (dropped === 0 && kept.length === raw.length) {
		return text;
	}
	const total = dropped + raw.length;
	const keptStart = dropped > 0 ? total - kept.length + 1 : 1;
	const marker = `[truncated, kept chars ${keptStart}-${keptStart + kept.length - 1} of ${total}]`;
	// A whitespace-only line is not an event, and a tail cut does not change that:
	// the marker alone would say nothing a reader can act on. A carry drop is
	// different, because characters really did go, so the loss still has to report.
	if (text === "") {
		return dropped > 0 ? marker : "";
	}
	return `${text} ${marker}`;
}

function describeTermination(
	code: number | null,
	signal: NodeJS.Signals | null,
): string {
	if (signal !== null) {
		return `on signal ${signal}`;
	}
	if (code !== null) {
		return `with code ${code}`;
	}
	return "for an unknown reason";
}

/**
 * Kill the shell and everything it started. No-op once the tree is gone.
 *
 * Killing the direct child is not enough: a poll loop spends nearly all its time
 * inside a `sleep` that the shell started, and that sleep keeps the pipe open
 * after the shell dies. The negative pid targets the process group created by the
 * `detached` spawn option; Windows has no process groups, hence taskkill /T.
 */
function killProcessTree(child: ChildProcess): void {
	const pid = child.pid;
	if (pid === undefined) {
		return;
	}
	if (process.platform === "win32") {
		const killer = spawn("taskkill", ["/F", "/T", "/PID", String(pid)], {
			stdio: "ignore",
			windowsHide: true,
		});
		killer.on("error", () => {
			// Nothing better to try, and a failed kill must not crash the session.
		});
		return;
	}
	try {
		process.kill(-pid, "SIGKILL");
	} catch {
		// The group is already gone, or the shell never became its leader.
		child.kill("SIGKILL");
	}
}
