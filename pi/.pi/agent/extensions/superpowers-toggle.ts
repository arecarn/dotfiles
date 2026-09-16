/**
 * Mid-session on/off switch for obra/superpowers' bootstrap prompt.
 *
 * Superpowers has no built-in toggle: its own `.pi/extensions/superpowers.ts`
 * injects an `<EXTREMELY_IMPORTANT>` "You have superpowers" block once per
 * session (again after compaction), and the only way to stop it is removing
 * the whole package -- which also drops its skills. See
 * docs/adr/ for the decision behind this file and why Claude Code gets no
 * equivalent (its SessionStart hook lives in superpowers' own installed
 * plugin directory, which this repo does not own and Claude Code will not let
 * a second hook cancel).
 *
 * This works in pi because superpowers' injector has a documented escape
 * hatch: it skips injecting if any message already carries the marker string
 * `superpowers:using-superpowers bootstrap for pi`. Pi loads user-scope
 * extensions (this one, from ~/.pi/agent/extensions/) before package-scope
 * extensions (superpowers' own), and `context` handlers run in that load
 * order, chained -- each handler sees the previous handler's output. So this
 * extension's own `context` handler runs first on every LLM call within a
 * turn, and when the shared flag is off, it seeds a decoy message carrying
 * that marker so superpowers' own handler, running right after, sees the
 * marker already present and stands down.
 *
 * Reads the same flag file `manage/superpowers_toggle.py` writes, so
 * `superpowers-toggle off` (any harness, any shell) and this extension's own
 * `/superpowers-toggle` command agree. The decoy is regenerated fresh each
 * call rather than cached, because the flag can flip between calls within one
 * session -- that is the entire point of a mid-session toggle.
 */

import {
	existsSync,
	mkdirSync,
	readFileSync,
	unlinkSync,
	writeFileSync,
} from "node:fs";
import { homedir } from "node:os";
import { join } from "node:path";
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

// Mirrors superpowers' own BOOTSTRAP_MARKER. Duplicated rather than imported:
// pi packages load with separate module roots (see docs/packages.md), so
// there is no shared module to import it from. A future superpowers release
// renaming this string silently re-enables its bootstrap; that is the known
// fragility of relying on another package's internal marker, noted above.
const SUPERPOWERS_BOOTSTRAP_MARKER =
	"superpowers:using-superpowers bootstrap for pi";
const DECOY_MARKER = "superpowers-toggle: suppressing bootstrap while off";

const STATE_DIR_ENV = "SUPERPOWERS_TOGGLE_STATE_DIR";
const STATE_FILE_NAME = "superpowers-bootstrap";

/** The state directory: env var override, then the XDG default -- matches
 * manage/superpowers_toggle.py's state_dir(). */
export function stateDir(env: NodeJS.ProcessEnv = process.env): string {
	const override = env[STATE_DIR_ENV];
	if (override) return override;
	const xdg = env.XDG_STATE_HOME || join(homedir(), ".local", "state");
	return join(xdg, "ai-skills");
}

/** Whether the bootstrap should inject: true unless the flag file says "off".
 * Absent file means enabled, matching manage/superpowers_toggle.py. */
export function isEnabled(dir: string): boolean {
	const path = join(dir, STATE_FILE_NAME);
	if (!existsSync(path)) return true;
	try {
		return readFileSync(path, "utf8").trim() !== "off";
	} catch {
		// An unreadable flag file must not block the session; treat as enabled,
		// the same fail-open rule the Claude Code hook counterpart follows.
		return true;
	}
}

function messageContainsMarker(message: unknown, marker: string): boolean {
	const content = (message as { content?: unknown } | undefined)?.content;
	if (typeof content === "string") return content.includes(marker);
	if (!Array.isArray(content)) return false;
	return content.some(
		(part) =>
			part &&
			typeof part === "object" &&
			(part as { type?: unknown }).type === "text" &&
			typeof (part as { text?: unknown }).text === "string" &&
			(part as { text: string }).text.includes(marker),
	);
}

export default function superpowersToggle(pi: ExtensionAPI): void {
	pi.on("context", async (event) => {
		const dir = stateDir();
		if (isEnabled(dir)) return;
		// Already suppressed this turn (our own decoy, or superpowers' own
		// bootstrap already present from before the flag was flipped off) --
		// nothing more to do.
		if (
			event.messages.some((m) =>
				messageContainsMarker(m, SUPERPOWERS_BOOTSTRAP_MARKER),
			)
		) {
			return;
		}
		const decoy = {
			role: "user" as const,
			content: [
				{
					type: "text" as const,
					text: `${DECOY_MARKER}\n${SUPERPOWERS_BOOTSTRAP_MARKER}`,
				},
			],
			timestamp: Date.now(),
		};
		return { messages: [decoy, ...event.messages] };
	});

	pi.registerCommand("superpowers-toggle", {
		description: "Flip the shared superpowers-bootstrap flag on or off",
		handler: async (args, ctx) => {
			const dir = stateDir();
			const next = args.trim();
			let enabled: boolean;
			if (next === "on" || next === "off") {
				enabled = next === "on";
			} else {
				enabled = !isEnabled(dir);
			}
			const path = join(dir, STATE_FILE_NAME);
			if (enabled) {
				try {
					unlinkSync(path);
				} catch {
					// Already absent (already enabled) -- nothing to remove.
				}
			} else {
				mkdirSync(dir, { recursive: true });
				writeFileSync(path, "off");
			}
			ctx.ui.notify(
				`superpowers bootstrap ${enabled ? "enabled" : "disabled"} (takes effect on the next injection point: next turn, or next compaction if it already fired this session)`,
				"info",
			);
		},
	});
}
