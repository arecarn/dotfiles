/**
 * agent-knowledge: tell the session which OKF bundles apply, once.
 *
 * Reference material lives in OKF bundles rather than in AGENTS.md, so the model
 * is shown a catalog of *root indexes* and reads a concept only when a task
 * needs one. That is the whole point: a large corpus costs a catalog, not a
 * context window.
 *
 * The catalog is injected once per session as a persistent custom message, not
 * appended to every prompt:
 *   - Persistent, so it survives the turn it was added in and stays available
 *     to later turns without being re-sent.
 *   - Once, keyed off the *model-visible* context rather than branch history, so
 *     a resumed session does not get a second copy while a compacted one that
 *     lost the first does.
 *
 * Bundle activation lives in the CLI (see resolver.ts), shared with the Claude
 * Code and OpenCode adapters.
 */

import type {
	ExtensionAPI,
	ExtensionCommandContext,
	ExtensionContext,
} from "@earendil-works/pi-coding-agent";
import { Type } from "typebox";
import { read, resolve, status } from "./resolver.js";

// Identifies our entries in session history, so the "have we injected?" check
// can find them and a reload can tell its own message from someone else's.
const CUSTOM_TYPE = "agent-knowledge";

/**
 * Whether the catalog is already in the context the model will see.
 *
 * Deliberately `buildContextEntries()` and not `getEntries()`/`getBranch()`:
 * compaction leaves the original entry in branch history while rebuilding model
 * context without it, so branch history would report a catalog the model can no
 * longer read. See
 * docs/gotchas/pi-branch-history-still-shows-context-compaction-dropped.md.
 */
function catalogInContext(ctx: ExtensionContext): boolean {
	for (const entry of ctx.sessionManager.buildContextEntries()) {
		if (entry.type === "custom_message" && entry.customType === CUSTOM_TYPE) {
			return true;
		}
	}
	return false;
}

export default function agentKnowledge(pi: ExtensionAPI): void {
	pi.on("before_agent_start", async (_event, ctx) => {
		if (catalogInContext(ctx)) return;

		// pi's own trust decision gates the project bundle, which is
		// repository-controlled content, on top of the resolver's project_roots
		// allowlist. Configured personal and work bundles are unaffected: the user
		// declared those themselves.
		const trusted = ctx.isProjectTrusted();
		const result = await resolve(ctx.cwd, { withProject: trusted });
		if (!result) return;

		// Reported before the catalog check, not after: a malformed bundles.yaml
		// yields diagnostics and *no* catalog, and that is the failure most worth
		// telling the user about. Local-only, because an unusable bundle names its
		// path -- exactly what must not reach the model or the transcript.
		if (ctx.hasUI) {
			for (const diagnostic of result.diagnostics) {
				ctx.ui.notify(`agent-knowledge: ${diagnostic.message}`, "warning");
			}
		}

		if (!result.catalog) return;

		return {
			message: {
				customType: CUSTOM_TYPE,
				content: result.catalog,
				// Shown in the transcript: knowledge the model was given silently is
				// knowledge nobody can audit when an answer cites it.
				display: true,
			},
		};
	});

	pi.registerTool({
		name: "knowledge_read",
		label: "Read knowledge",
		description: [
			"Read one Markdown document from an active agent-knowledge bundle.",
			"",
			"Use the bundle id from the knowledge catalog and a link target from that",
			"bundle's index. Pass source when following a link found inside a nested",
			"document, so a relative target resolves from the right directory.",
			"",
			"Only active bundles are readable, and only Markdown inside them.",
		].join("\n"),
		promptSnippet:
			"Read a Markdown document from an active agent-knowledge bundle",
		promptGuidelines: [
			"Use knowledge_read to open a document listed in the knowledge catalog instead of guessing its filesystem path.",
			"Read a knowledge document only when its description matches the task at hand.",
		],
		parameters: Type.Object({
			bundle: Type.String({
				description: "Bundle id from the knowledge catalog, e.g. 'project'",
			}),
			target: Type.String({
				description: "Link target to read, e.g. 'ops/release.md' or 'ops/'",
			}),
			source: Type.Optional(
				Type.String({
					description:
						"Document the link came from, for relative targets (default: index.md)",
				}),
			),
		}),
		async execute(_toolCallId, params, _signal, _onUpdate, ctx) {
			const result = await read(
				ctx.cwd,
				params.bundle,
				params.target,
				params.source,
			);
			if (!result) {
				return {
					content: [
						{ type: "text", text: "agent-knowledge is not available here." },
					],
					isError: true,
					details: {},
				};
			}
			if (result.error || result.content === null) {
				return {
					content: [
						{
							type: "text",
							text: `Cannot read ${params.target} from ${params.bundle}: ${result.error}`,
						},
					],
					isError: true,
					details: { error: result.error },
				};
			}
			return {
				content: [{ type: "text", text: result.content }],
				details: { bundle: result.bundle_id, path: result.path },
			};
		},
	});

	pi.registerCommand("knowledge", {
		description: "Show which agent-knowledge bundles apply here",
		handler: async (_args, ctx: ExtensionCommandContext) => {
			const report = await status(ctx.cwd);
			if (!report) {
				ctx.ui.notify("agent-knowledge is not available here.", "warning");
				return;
			}
			// Paths and inactive bundles go to the UI only, never into context.
			const lines = report.bundles.map(
				(bundle) =>
					`${bundle.active ? "active  " : "inactive"} ${bundle.id} (${bundle.reason}) ${bundle.path}`,
			);
			for (const diagnostic of report.diagnostics) {
				lines.push(`problem  ${diagnostic.message}`);
			}
			ctx.ui.notify(
				lines.length > 0
					? lines.join("\n")
					: `No knowledge bundles configured (${report.config_dir})`,
				"info",
			);
		},
	});

	pi.registerCommand("knowledge-reload", {
		description:
			"Re-read agent-knowledge bundles and inject the current catalog",
		handler: async (_args, ctx: ExtensionCommandContext) => {
			const result = await resolve(ctx.cwd);
			if (!result?.catalog) {
				ctx.ui.notify("No knowledge bundles apply here.", "info");
				return;
			}
			// A reload is the user asking for the current catalog, so it is appended
			// unconditionally; the newest entry is the one that applies.
			pi.sendMessage({
				customType: CUSTOM_TYPE,
				content: result.catalog,
				display: true,
			});
			ctx.ui.notify(
				`Reloaded knowledge: ${result.bundles.map((b) => b.id).join(", ")}`,
				"info",
			);
		},
	});
}
