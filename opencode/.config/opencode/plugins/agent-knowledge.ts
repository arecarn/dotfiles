/**
 * agent-knowledge for OpenCode: name the applicable bundles, read one on demand.
 *
 * OpenCode's system-transform hook runs for every physical model request, so the
 * catalog is resolved once per session and cached, then appended to each request
 * from that cache. Resolving per request would re-read the bundles every turn;
 * appending from the cache keeps exactly one copy in front of the model.
 *
 * The cache deliberately survives compaction: a new instruction epoch should
 * restore what the model had rather than re-read disk. Only an explicit reload
 * (`agent-knowledge resolve` from the CLI, or a new session) picks up edits.
 *
 * Bundle selection lives in the CLI, shared with the pi and Claude Code
 * adapters, so all three agree on which knowledge applies here.
 *
 * TypeScript rather than JavaScript because this repo's lint only reaches *.ts;
 * the types below are local for the same reason -- @opencode-ai/plugin is not a
 * dependency here, and one plugin is not worth making it one.
 */

import { execFile } from "node:child_process";
import { homedir } from "node:os";
import { join } from "node:path";
import { promisify } from "node:util";

const run = promisify(execFile);

// Stow links the launcher here; an unstowed machine simply has no knowledge.
const CLI = join(homedir(), ".local", "bin", "agent-knowledge");
const TIMEOUT_MS = 10_000;

interface ResolvePayload {
	catalog: string | null;
}

interface ReadPayload {
	content: string | null;
	error: string | null;
}

interface PluginInput {
	directory: string;
	worktree?: string;
}

/** Run one CLI operation, or return undefined when it is unusable. */
async function invoke<T>(args: string[], cwd: string): Promise<T | undefined> {
	try {
		const { stdout } = await run(CLI, args, { cwd, timeout: TIMEOUT_MS });
		return JSON.parse(stdout) as T;
	} catch (error) {
		// A refused read still prints a payload naming the reason, so parse stdout
		// before giving up. Anything else means no knowledge is available here.
		const stdout = (error as { stdout?: string }).stdout;
		if (stdout) {
			try {
				return JSON.parse(stdout) as T;
			} catch {
				return undefined;
			}
		}
		return undefined;
	}
}

export const AgentKnowledge = async ({ directory, worktree }: PluginInput) => {
	// The worktree is what makes project knowledge branch-local; `directory` is
	// the fallback for a session outside a repository.
	const cwd = worktree || directory;
	const catalogs = new Map<string, string | null>();

	const catalogFor = async (sessionID: string): Promise<string | null> => {
		const cached = catalogs.get(sessionID);
		if (cached !== undefined) return cached;
		const result = await invoke<ResolvePayload>(["resolve"], cwd);
		const catalog = result?.catalog ?? null;
		catalogs.set(sessionID, catalog);
		return catalog;
	};

	return {
		"experimental.chat.system.transform": async (
			input: { sessionID?: string },
			output: { system: string[] },
		): Promise<void> => {
			const catalog = await catalogFor(input.sessionID ?? "");
			if (catalog) output.system.push(catalog);
		},

		event: async ({
			event,
		}: {
			event: { type: string; properties?: { info?: { id?: string } } };
		}): Promise<void> => {
			// Drop cached state with the session it belongs to, so a long-lived
			// OpenCode process does not accumulate catalogs for dead sessions.
			if (event.type === "session.deleted") {
				const id = event.properties?.info?.id;
				if (id) catalogs.delete(id);
			}
		},

		tool: {
			knowledge_read: {
				description: [
					"Read one Markdown document from an active agent-knowledge bundle.",
					"Use the bundle id from the knowledge catalog and a link target from",
					"that bundle's index. Pass source when following a link inside a",
					"nested document so a relative target resolves correctly.",
				].join(" "),
				args: {
					bundle: { type: "string", description: "Bundle id from the catalog" },
					target: {
						type: "string",
						description: "Link target, e.g. ops/release.md",
					},
					source: {
						type: "string",
						description: "Document the link came from (default: index.md)",
						optional: true,
					},
				},
				async execute(args: {
					bundle: string;
					target: string;
					source?: string;
				}): Promise<string> {
					const argv = [
						"read",
						"--bundle",
						args.bundle,
						"--target",
						args.target,
					];
					if (args.source) argv.push("--source", args.source);
					const result = await invoke<ReadPayload>(argv, cwd);
					if (!result) return "agent-knowledge is not available here.";
					if (result.error || result.content === null) {
						return `Cannot read ${args.target} from ${args.bundle}: ${result.error}`;
					}
					return result.content;
				},
			},
		},
	};
};
