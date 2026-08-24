/**
 * Background process behind one monitor: spawn, line splitting, truncation, rate
 * limiting, exit handling.
 *
 * Deliberately free of pi API calls, so what a monitor emits can be checked by
 * reading this file alone. Everything session-shaped lives in registry.ts and
 * index.ts.
 */

import { type ChildProcess, spawn } from "node:child_process";

/** stdout lines longer than this are cut, and the cut is marked in the event. */
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
	let stdoutRest = "";
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
	// one event.
	const emitLine = (line: string): void => {
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
		emit(truncateLine(line));
	};

	child.stdout?.setEncoding("utf8");
	child.stdout?.on("data", (chunk: string) => {
		const lines = (stdoutRest + chunk).split("\n");
		stdoutRest = lines.pop() ?? "";
		for (const line of lines) {
			const text = line.trim();
			if (text !== "") {
				emitLine(text);
			}
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
		const trailing = stdoutRest.trim();
		stdoutRest = "";
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

function truncateLine(line: string): string {
	if (line.length <= MAX_LINE_CHARS) {
		return line;
	}
	return `${line.slice(0, MAX_LINE_CHARS)} [truncated, ${line.length} chars total]`;
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
