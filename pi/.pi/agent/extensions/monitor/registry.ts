/**
 * The monitors of one session: id assignment, caps, the wake default, disarm and
 * shutdown. Holds no pi wiring beyond the context it lends to delivery.
 */

import type { ExtensionContext } from "@earendil-works/pi-coding-agent";
import {
	type MonitorExit,
	type MonitorProcess,
	startMonitorProcess,
} from "./runner.ts";

export type MonitorStatus = "running" | "done" | "failed" | "disarmed";

export type Monitor = {
	/** "m1", "m2", ... assigned in arm order. */
	id: string;
	label: string;
	command: string;
	cwd: string;
	/** undefined = unlimited; 1 = one-shot. */
	maxEvents?: number;
	/** Effective value, after the derived default applied in arm(). */
	wake: boolean;
	eventsSeen: number;
	status: MonitorStatus;
};

/** Cap on monitors in "running" state, so a session cannot arm processes without limit. */
export const MAX_RUNNING_MONITORS = 8;

export type ArmRequest = {
	command: string;
	label?: string;
	maxEvents?: number;
	/** Omitted means "derive it": see the rule in arm(). */
	wake?: boolean;
	/** Already resolved to an absolute path by the caller. */
	cwd: string;
};

/**
 * Called once per event, with the monitor's own state and the most recently seen
 * ExtensionContext (undefined before any tool call, command, or session start).
 */
export type MonitorEventHandler = (
	monitor: Monitor,
	text: string,
	ctx: ExtensionContext | undefined,
) => void;

/** Called after a transition that can change the set of running monitors. */
export type MonitorChangeHandler = (
	monitors: Monitor[],
	ctx: ExtensionContext | undefined,
) => void;

export class MonitorRegistry {
	private readonly monitors = new Map<string, Monitor>();
	private readonly processes = new Map<string, MonitorProcess>();
	private readonly deliverEvent: MonitorEventHandler;
	private readonly reportChange: MonitorChangeHandler;
	private nextId = 1;
	private latestContext: ExtensionContext | undefined;

	constructor(
		onEvent: MonitorEventHandler,
		onChange: MonitorChangeHandler = () => {},
	) {
		this.deliverEvent = onEvent;
		this.reportChange = onChange;
	}

	/**
	 * Remember the context of the most recent tool call, command, or session start.
	 *
	 * Quiet delivery calls ctx.ui.notify from a stdout callback that has no context
	 * of its own, so one has to be kept here. shutdown() drops it, which is what
	 * stops the reference outliving the session that produced it.
	 */
	noteContext(ctx: ExtensionContext): void {
		this.latestContext = ctx;
	}

	/**
	 * Start a monitor and return it. Throws at MAX_RUNNING_MONITORS.
	 *
	 * Call this only from the tool or from the command handler. Extension factories
	 * also run in invocations that never start a session, so a factory must not
	 * reach a spawn.
	 */
	arm(request: ArmRequest): Monitor {
		const running = this.list().filter(
			(monitor) => monitor.status === "running",
		).length;
		if (running >= MAX_RUNNING_MONITORS) {
			throw new Error(
				`${MAX_RUNNING_MONITORS} monitors are already running; disarm one before arming another`,
			);
		}

		const id = `m${this.nextId}`;
		this.nextId += 1;
		const monitor: Monitor = {
			id,
			// Normalized even when given: a label holding a newline would break both the
			// one-line-per-monitor listing and the event prefix.
			label: defaultLabel(request.label ?? request.command),
			command: request.command,
			cwd: request.cwd,
			maxEvents: request.maxEvents,
			// The wake default: an explicit wake wins; otherwise a one-shot monitor
			// wakes, because its single event is the answer somebody is waiting for,
			// and a repeating monitor does not, because it would interrupt every turn.
			// watch-ci depends on this: it arms with maxEvents 1 and no wake.
			wake: request.wake ?? request.maxEvents === 1,
			eventsSeen: 0,
			status: "running",
		};
		this.monitors.set(id, monitor);
		this.processes.set(
			id,
			startMonitorProcess(
				{ command: monitor.command, cwd: monitor.cwd },
				{
					onEvent: (text) => this.recordEvent(monitor, text),
					onExit: (exit) => this.recordExit(monitor, exit),
				},
			),
		);
		this.notifyChange();
		return monitor;
	}

	/** Every monitor armed in this session, in arm order, live objects and not copies. */
	list(): Monitor[] {
		return [...this.monitors.values()];
	}

	/**
	 * Disarm one monitor. Returns it, or undefined for an unknown id. A monitor that
	 * is no longer running is returned unchanged.
	 */
	disarm(id: string): Monitor | undefined {
		const monitor = this.monitors.get(id);
		if (monitor === undefined) {
			return undefined;
		}
		if (monitor.status === "running") {
			this.stop(monitor, "disarmed");
		}
		return monitor;
	}

	/** Disarm every running monitor and return the ones stopped, so a repeat call returns none. */
	disarmAll(): Monitor[] {
		const stopped = this.list().filter(
			(monitor) => monitor.status === "running",
		);
		for (const monitor of stopped) {
			this.stop(monitor, "disarmed");
		}
		return stopped;
	}

	/**
	 * Session teardown: disarm everything and drop the stored context. Idempotent,
	 * so calling it twice is safe.
	 */
	shutdown(): void {
		this.disarmAll();
		this.latestContext = undefined;
	}

	private recordEvent(monitor: Monitor, text: string): void {
		// A rate-limit flush can land just after an auto-disarm; a monitor that is no
		// longer running is silent by definition.
		if (monitor.status !== "running") {
			return;
		}
		monitor.eventsSeen += 1;
		this.deliverEvent(monitor, text, this.latestContext);
		if (
			monitor.maxEvents !== undefined &&
			monitor.eventsSeen >= monitor.maxEvents
		) {
			// Quota filled, so the monitor did its job: "done", not "disarmed".
			this.stop(monitor, "done");
		}
	}

	private recordExit(monitor: Monitor, exit: MonitorExit): void {
		this.processes.delete(monitor.id);
		// A monitor we killed already holds its final status; only a process that
		// ended on its own decides its status here.
		if (monitor.status !== "running") {
			return;
		}
		monitor.status =
			exit.signal === null && exit.code === 0 ? "done" : "failed";
		this.notifyChange();
	}

	private stop(monitor: Monitor, status: MonitorStatus): void {
		monitor.status = status;
		const running = this.processes.get(monitor.id);
		this.processes.delete(monitor.id);
		running?.kill();
		this.notifyChange();
	}

	private notifyChange(): void {
		this.reportChange(this.list(), this.latestContext);
	}
}

/** A monitor's label on one shortened line: an explicit label, or its command. */
function defaultLabel(label: string): string {
	const oneLine = label.replace(/\s+/g, " ").trim();
	return oneLine.length <= 40 ? oneLine : `${oneLine.slice(0, 40)}...`;
}
