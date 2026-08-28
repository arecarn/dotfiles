/** Show Pi's active background work as a compact Herdr agent-row token. */

import { randomUUID } from "node:crypto";
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

const SOURCE = "pi-work-status";
const TOKEN = "work_status";
const REFRESH_MS = 1000;

type WorkKind = "monitors" | "background" | "agents";
export type WorkCounts = Record<WorkKind, number>;
type EventBus = ExtensionAPI["events"];

export function formatWorkStatus(counts: WorkCounts): string | undefined {
	const parts = [
		counts.monitors > 0 ? `M${counts.monitors}` : undefined,
		counts.background > 0 ? `B${counts.background}` : undefined,
		counts.agents > 0 ? `A${counts.agents}` : undefined,
	].filter((part): part is string => part !== undefined);
	return parts.length === 0 ? undefined : parts.join(" ");
}

export class WorkStatus {
	private readonly counts: WorkCounts = {
		monitors: 0,
		background: 0,
		agents: 0,
	};
	private readonly publish: (value: string | undefined) => void;

	constructor(publish: (value: string | undefined) => void) {
		this.publish = publish;
	}

	set(kind: WorkKind, count: number): void {
		const normalized = Number.isFinite(count)
			? Math.max(0, Math.floor(count))
			: 0;
		if (this.counts[kind] === normalized) return;
		this.counts[kind] = normalized;
		this.publish(formatWorkStatus(this.counts));
	}
}

export default function herdrWorkStatus(pi: ExtensionAPI): void {
	const paneId = process.env.HERDR_PANE_ID;
	if (process.env.HERDR_ENV !== "1" || !paneId) return;

	const targetPaneId = paneId;
	const herdrBin = process.env.HERDR_BIN_PATH || "herdr";
	let rootSession = false;
	let refreshTimer: NodeJS.Timeout | undefined;
	let publishInFlight = false;
	let queuedValue: string | undefined;
	let hasQueuedValue = false;
	let seq = Date.now() * 1000;

	const publish = (value: string | undefined): void => {
		queuedValue = value;
		hasQueuedValue = true;
		if (!publishInFlight) void drainPublications();
	};
	const status = new WorkStatus(publish);

	async function drainPublications(): Promise<void> {
		publishInFlight = true;
		try {
			while (hasQueuedValue) {
				const value = queuedValue;
				hasQueuedValue = false;
				seq += 1;
				const args: string[] = [
					"pane",
					"report-metadata",
					targetPaneId,
					"--source",
					SOURCE,
					"--seq",
					String(seq),
					value === undefined ? "--clear-token" : "--token",
					value === undefined ? TOKEN : `${TOKEN}=${value}`,
				];
				try {
					await pi.exec(herdrBin, args, { timeout: 5000 });
				} catch {
					// Display-only status must never disrupt the Pi session.
				}
			}
		} finally {
			publishInFlight = false;
			if (hasQueuedValue) void drainPublications();
		}
	}

	const monitorOff = pi.events.on("dotfiles:monitor-count", (raw) => {
		if (!rootSession) return;
		const count = readNumber(raw, "running");
		if (count !== undefined) status.set("monitors", count);
	});

	async function refresh(): Promise<void> {
		if (!rootSession) return;
		const [background, agents] = await Promise.all([
			requestBackgroundCount(pi.events),
			requestAgentCount(pi.events),
		]);
		if (!rootSession) return;
		if (background !== undefined) status.set("background", background);
		if (agents !== undefined) status.set("agents", agents);
	}

	pi.on("session_start", (_event, ctx) => {
		if (ctx.mode !== "tui") return;
		rootSession = true;
		void refresh();
		refreshTimer = setInterval(() => void refresh(), REFRESH_MS);
		refreshTimer.unref?.();
	});

	pi.on("session_shutdown", () => {
		rootSession = false;
		if (refreshTimer) clearInterval(refreshTimer);
		refreshTimer = undefined;
		status.set("monitors", 0);
		status.set("background", 0);
		status.set("agents", 0);
	});

	pi.on("session_shutdown", () => monitorOff());
}

async function requestBackgroundCount(
	events: EventBus,
): Promise<number | undefined> {
	const requestId = randomUUID();
	const response = await requestOnce(
		events,
		"pi-background-tasks:response:v1",
		() =>
			events.emit("pi-background-tasks:request:v1", {
				schema_version: "pi-background-tasks.extension-request.v1",
				request_id: requestId,
				operation: "status",
				payload: {},
			}),
		(raw) => readString(raw, "request_id") === requestId,
	);
	if (
		!isRecord(response) ||
		response.ok !== true ||
		!isRecord(response.result)
	) {
		return undefined;
	}
	const tasks = response.result.tasks;
	if (!Array.isArray(tasks)) return undefined;
	return tasks.filter((task) => isRecord(task) && task.status === "running")
		.length;
}

async function requestAgentCount(
	events: EventBus,
): Promise<number | undefined> {
	const requestId = randomUUID();
	const replyEvent = `subagents:rpc:v1:reply:${requestId}`;
	const response = await requestOnce(
		events,
		replyEvent,
		() =>
			events.emit("subagents:rpc:v1:request", {
				version: 1,
				requestId,
				method: "status",
				params: {},
			}),
		() => true,
	);
	if (
		!isRecord(response) ||
		response.success !== true ||
		!isRecord(response.data)
	) {
		return undefined;
	}
	const fleet = response.data.fleet;
	return isRecord(fleet) ? readNumber(fleet, "totalActive") : undefined;
}

function requestOnce(
	events: EventBus,
	channel: string,
	emit: () => void,
	matches: (raw: unknown) => boolean,
): Promise<unknown> {
	return new Promise((resolve) => {
		let settled = false;
		const off = events.on(channel, (raw) => {
			if (!matches(raw) || settled) return;
			settled = true;
			clearTimeout(timeout);
			off();
			resolve(raw);
		});
		const timeout = setTimeout(() => {
			if (settled) return;
			settled = true;
			off();
			resolve(undefined);
		}, 500);
		timeout.unref?.();
		emit();
	});
}

function isRecord(value: unknown): value is Record<string, unknown> {
	return typeof value === "object" && value !== null;
}

function readNumber(value: unknown, key: string): number | undefined {
	if (!isRecord(value)) return undefined;
	return typeof value[key] === "number" ? value[key] : undefined;
}

function readString(value: unknown, key: string): string | undefined {
	if (!isRecord(value)) return undefined;
	return typeof value[key] === "string" ? value[key] : undefined;
}
