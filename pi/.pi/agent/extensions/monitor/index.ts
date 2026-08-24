/**
 * monitor: run a shell command in the background and turn its output into
 * session events, so a wait that takes minutes does not hold the session.
 *
 * Nothing spawns at load time. Extension factories also run in invocations that
 * never start a session, so a monitor starts only from the tool or the command.
 */

import { resolve } from "node:path";
import { StringEnum } from "@earendil-works/pi-ai";
import type {
	ExtensionAPI,
	ExtensionCommandContext,
	ExtensionContext,
} from "@earendil-works/pi-coding-agent";
import { Type } from "typebox";
import { type Monitor, MonitorRegistry } from "./registry.js";

export default function (pi: ExtensionAPI) {
	// Event text names the monitor, because several can run at once and their
	// events arrive interleaved.
	const deliver = (
		monitor: Monitor,
		text: string,
		ctx: ExtensionContext | undefined,
	): void => {
		const message = {
			customType: "monitor",
			content: `[monitor ${monitor.id} ${monitor.label}] ${text}`,
			display: true,
		};
		// This runs in a stdout listener, so a throw here is an uncaughtException that
		// takes the pi process down rather than a tool error somebody sees. There is no
		// caller to rethrow to, and a lost monitor event must not cost the session.
		try {
			if (monitor.wake) {
				// followUp waits for the current turn's tools to finish rather than
				// interrupting them; triggerTurn is what makes an idle session respond.
				pi.sendMessage(message, { deliverAs: "followUp", triggerTurn: true });
				return;
			}
			if (ctx?.hasUI) {
				ctx.ui.notify(message.content, "info");
			}
			pi.sendMessage(message, { deliverAs: "nextTurn" });
		} catch {
			// Deliberately silent: the only channels for saying so are the two that just
			// failed.
		}
	};

	const registry = new MonitorRegistry(deliver);

	pi.registerTool({
		name: "monitor",
		label: "Monitor",
		description: [
			"Run a shell command in the background and report its output as session events.",
			"Each non-blank stdout line is one event; stderr is kept for diagnostics only.",
			"A command that exits having produced no output still reports one event naming its exit code.",
			"",
			"Actions:",
			'- arm: start a monitor. Returns its id, label, and effective "wake" value.',
			"- list: show every monitor armed in this session.",
			'- disarm: stop the monitor named by id, or every running monitor with id "all".',
			"",
			"Monitors are session-scoped: they do not survive a session switch, resume, or fork.",
		].join("\n"),
		promptSnippet:
			"Arm, list, or disarm background commands whose output is delivered as session events",
		promptGuidelines: [
			"Use monitor instead of a foreground bash call for a command that waits, such as a CI poll loop, so the wait does not block the session.",
			"Arm monitor with maxEvents 1 when a single line answers the question; that also makes the monitor wake the session as soon as the line arrives.",
			"Disarm a monitor through monitor once its answer has arrived, and do not expect a monitor armed in an earlier session to still exist.",
		],
		parameters: Type.Object({
			action: StringEnum(["arm", "list", "disarm"] as const, {
				description:
					"What to do: arm a new monitor, list monitors, or disarm one",
			}),
			command: Type.Optional(
				Type.String({ description: "arm: the shell command to run" }),
			),
			label: Type.Optional(
				Type.String({
					description:
						"arm: short name shown in events and listings. Defaults to the command",
				}),
			),
			maxEvents: Type.Optional(
				Type.Integer({
					minimum: 1,
					description:
						"arm: disarm after this many events. Omit for unlimited, 1 for a one-shot monitor",
				}),
			),
			wake: Type.Optional(
				Type.Boolean({
					description:
						"arm: deliver events at once and trigger a turn. Defaults to true when maxEvents is 1, false otherwise",
				}),
			),
			cwd: Type.Optional(
				Type.String({
					description:
						"arm: working directory, absolute or relative to the session directory. Defaults to the session directory",
				}),
			),
			id: Type.Optional(
				Type.String({ description: 'disarm: the monitor id, or "all"' }),
			),
		}),
		async execute(_toolCallId, params, _signal, _onUpdate, ctx) {
			registry.noteContext(ctx);
			switch (params.action) {
				case "arm": {
					const command = params.command?.trim();
					if (command === undefined || command === "") {
						throw new Error("monitor arm needs a command");
					}
					const monitor = registry.arm({
						command,
						label: params.label,
						maxEvents: params.maxEvents,
						wake: params.wake,
						// Some models prefix a path with @; pi's built-in tools strip it, so a
						// custom tool taking a path has to as well.
						cwd: resolve(ctx.cwd, params.cwd?.replace(/^@/, "") ?? "."),
					});
					return {
						content: [
							{
								type: "text",
								text: `Armed ${monitor.id} "${monitor.label}" in ${monitor.cwd}, wake ${monitor.wake}, maxEvents ${describeMaxEvents(monitor)}`,
							},
						],
						details: { ...monitor },
					};
				}
				case "list": {
					const monitors = registry.list();
					return {
						content: [
							{
								type: "text",
								text:
									monitors.length === 0
										? "No monitors armed in this session."
										: monitors.map(describeMonitor).join("\n"),
							},
						],
						details: { monitors: monitors.map((monitor) => ({ ...monitor })) },
					};
				}
				case "disarm": {
					const id = params.id?.trim();
					if (id === undefined || id === "") {
						throw new Error('monitor disarm needs an id, or "all"');
					}
					if (id === "all") {
						const stopped = registry.disarmAll();
						return {
							content: [
								{
									type: "text",
									text:
										stopped.length === 0
											? "No running monitors to disarm."
											: `Disarmed ${stopped.map((monitor) => monitor.id).join(", ")}.`,
								},
							],
							details: { disarmed: stopped.map((monitor) => monitor.id) },
						};
					}
					const monitor = registry.disarm(id);
					if (monitor === undefined) {
						throw new Error(`No monitor with id ${id}`);
					}
					return {
						content: [
							{
								type: "text",
								text: `Monitor ${monitor.id} is ${monitor.status}.`,
							},
						],
						details: { ...monitor },
					};
				}
			}
		},
	});

	pi.registerCommand("monitor", {
		description: "List, arm, or disarm background command monitors",
		handler: async (args, ctx) => {
			registry.noteContext(ctx);
			const request = args.trim();
			const separator = request.search(/\s/);
			const subcommand =
				separator === -1 ? request : request.slice(0, separator);
			const rest = separator === -1 ? "" : request.slice(separator + 1).trim();

			if (subcommand === "") {
				const monitors = registry.list();
				report(
					ctx,
					monitors.length === 0
						? "No monitors armed in this session."
						: monitors.map(describeMonitor).join("\n"),
				);
				return;
			}
			if (subcommand === "arm") {
				if (rest === "") {
					throw new Error("usage: /monitor arm <command>");
				}
				const monitor = registry.arm({ command: rest, cwd: ctx.cwd });
				report(
					ctx,
					`Armed ${monitor.id} "${monitor.label}", wake ${monitor.wake}, maxEvents ${describeMaxEvents(monitor)}`,
				);
				return;
			}
			if (subcommand === "disarm") {
				if (rest === "all") {
					const stopped = registry.disarmAll();
					report(
						ctx,
						stopped.length === 0
							? "No running monitors."
							: `Disarmed ${stopped.length}.`,
					);
					return;
				}
				const monitor = registry.disarm(rest);
				if (monitor === undefined) {
					throw new Error(`No monitor with id ${rest || "(none given)"}`);
				}
				report(ctx, `Monitor ${monitor.id} is ${monitor.status}.`);
				return;
			}
			throw new Error(
				`unknown subcommand "${subcommand}": use /monitor, /monitor arm <command>, or /monitor disarm <id|all>`,
			);
		},
	});

	// Capture the context here as well, so the one delivery holds always belongs to
	// the session now running rather than to whatever ran last.
	pi.on("session_start", (_event, ctx) => {
		registry.noteContext(ctx);
	});

	// Session switch, resume, and fork all fire this, and monitors deliberately do
	// not come back afterwards: their events belong to the session that armed them.
	// watch-ci states the same expectation for a rewritten SHA, whose old watch is
	// worthless anyway.
	pi.on("session_shutdown", () => {
		registry.shutdown();
	});
}

function describeMonitor(monitor: Monitor): string {
	return `${monitor.id} ${monitor.status} events ${monitor.eventsSeen}/${describeMaxEvents(monitor)} wake ${monitor.wake} "${monitor.label}"`;
}

function describeMaxEvents(monitor: Monitor): string {
	return monitor.maxEvents === undefined
		? "unlimited"
		: String(monitor.maxEvents);
}

/** Command output goes to the UI when there is one; print and JSON modes have none. */
function report(ctx: ExtensionCommandContext, text: string): void {
	if (ctx.hasUI) {
		ctx.ui.notify(text, "info");
	}
}
