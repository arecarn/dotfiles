/**
 * Push pi's session name into herdr's agent sidebar row.
 *
 * `/name` sets a pi-side display name that herdr never sees: the bundled
 * herdr-agent-state integration reports only lifecycle state and the session
 * path, so the sidebar keeps drawing the agent *kind* ("pi") for every pane.
 * This mirrors the name onto the focused pane's herdr metadata instead.
 *
 * Two herdr fields are written because neither alone suffices:
 *   - display_agent: free text, replaces "pi" in the sidebar's `agent` token.
 *     This is what you actually see.
 *   - agent name: the handle `herdr agent prompt|read|send-keys` accepts, so a
 *     named session is also addressable from the CLI. Constrained to
 *     [a-z][a-z0-9_-]{0,31}, hence the slug; skipped when a name cannot be
 *     slugified (e.g. all-punctuation input).
 *
 * Deliberately does nothing else. Tab, workspace, and git branch names are
 * yours; @henryqw/pi-herdr-rename is the package that also renames those and
 * generates titles with a model call.
 */

import type {
	ExtensionAPI,
	ExtensionContext,
} from "@earendil-works/pi-coding-agent";

// Namespaces this extension's writes so herdr can expire or override them
// independently of the bundled pi integration's own reports.
const SOURCE = "pi-session-name";

const AGENT_NAME_MAX = 32;

// A name this long is machine-generated rather than typed: pi's own subagent
// names are `subagent-<role>-<uuid>-<n>` at 58 characters. Such a name cannot
// produce a useful handle -- truncating to AGENT_NAME_MAX lands mid-uuid, and
// two subagents from one run share that prefix, so their handles collide -- and
// it overflows the sidebar it is meant to label.
const DISPLAY_NAME_MAX = 40;

/**
 * herdr agent names: lowercase start, then lowercase/digit/-/_ up to 32 chars.
 *
 * Returns undefined when the name cannot produce a usable handle, either because
 * nothing survives slugification or because truncation would cut an identifier
 * mid-token. Callers treat that as "set the display field only".
 */
function slugify(name: string): string | undefined {
	const slug = name
		.toLowerCase()
		.replace(/[^a-z0-9]+/g, "-")
		.replace(/^-+|-+$/g, "")
		.replace(/^[^a-z]+/, "");
	if (slug.length === 0) return undefined;
	if (slug.length > AGENT_NAME_MAX) return undefined;
	return slug;
}

export default function herdrSessionName(pi: ExtensionAPI): void {
	const paneId = process.env.HERDR_PANE_ID;
	// Outside herdr this extension has no target; a missing pane id also covers
	// headless modes, where there is no pane for herdr to draw. Returning here
	// registers no handlers at all, so a machine without herdr carries this file
	// inertly rather than erroring.
	if (process.env.HERDR_ENV !== "1" || !paneId) return;

	// The running server injects its own binary path. Preferring it over a bare
	// `herdr` keeps a stale copy earlier in PATH from talking to a newer server,
	// which is the same reason herdr's own agent hooks stopped using PATH.
	const herdrBin = process.env.HERDR_BIN_PATH || "herdr";

	// A rename supersedes any in-flight sync, which matters because each sync is
	// two sequential execs and `/name` can be typed repeatedly.
	let pending: AbortController | undefined;

	// Only the pane's own root TUI session may label the pane. A subagent runs in
	// the same pane and gets an auto-generated session name, so without this gate
	// it overwrites the row with its own id and leaves the session the user named
	// unlabelled. Set in session_start, which subagent sessions do not reach in
	// tui mode; the bundled herdr integration gates its reports the same way.
	let rootSession = false;

	const sync = async (
		name: string | undefined,
		ctx: ExtensionContext,
	): Promise<void> => {
		pending?.abort();
		const controller = new AbortController();
		pending = controller;
		const { signal } = controller;

		// Length is checked on the display field too, not just the handle: a
		// machine-generated name overflows the sidebar it is supposed to label.
		if (name && name.length > DISPLAY_NAME_MAX) return;

		const run = (args: string[]) =>
			pi.exec(herdrBin, args, { signal, timeout: 5000 });

		try {
			// Clearing both fields restores herdr's own detection ("pi").
			if (!name) {
				await run([
					"pane",
					"report-metadata",
					paneId,
					"--source",
					SOURCE,
					"--clear-display-agent",
				]);
				if (signal.aborted) return;
				await run(["agent", "rename", paneId, "--clear"]);
				return;
			}

			await run([
				"pane",
				"report-metadata",
				paneId,
				"--source",
				SOURCE,
				"--display-agent",
				name,
			]);
			if (signal.aborted) return;

			// Best-effort: the sidebar already shows the real name via
			// display_agent, so a name that will not slugify is not worth a
			// warning the user cannot act on.
			const slug = slugify(name);
			if (slug) await run(["agent", "rename", paneId, slug]);
		} catch (error) {
			if (signal.aborted) return;
			ctx.ui.notify(
				`herdr rename failed: ${error instanceof Error ? error.message : String(error)}`,
				"warning",
			);
		} finally {
			if (pending === controller) pending = undefined;
		}
	};

	pi.on("session_info_changed", (event, ctx) => {
		if (!rootSession) return;
		void sync(event.name, ctx);
	});

	// Resume and fork restore a session name without emitting
	// session_info_changed, and a new pane starts with herdr's own detection, so
	// reassert on startup rather than waiting for the next `/name`.
	pi.on("session_start", (_event, ctx) => {
		// TUI only: RPC, JSON and print modes are headless, so they own no pane
		// row to label even though they run in one.
		if (ctx.mode !== "tui") return;
		rootSession = true;
		const name = pi.getSessionName();
		if (name) void sync(name, ctx);
	});

	pi.on("session_shutdown", () => {
		pending?.abort();
		pending = undefined;
		rootSession = false;
	});
}
