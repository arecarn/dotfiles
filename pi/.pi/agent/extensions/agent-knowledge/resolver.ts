/**
 * Getting the knowledge catalog, from the CLI when it is there.
 *
 * Bundle activation, OKF validation, and read safety live in the CLI so that pi,
 * Claude Code, and OpenCode cannot drift apart on which knowledge applies here.
 * Mostly this module is transport: spawn, parse, translate a failure into
 * something the caller can render.
 *
 * When the CLI is absent it falls back to reading the project's own
 * `agents-knowledge/index.md` directly (see fallback.ts). A project bundle is
 * Markdown committed in the repo, so the extension should work on a machine that
 * has installed nothing -- the CLI adds structure on top: bundles configured
 * outside the workspace, an allowlist over which projects count, ordering across
 * several bundles, and constrained concept reads.
 *
 * The CLI is invoked by absolute path, because a session started anywhere -- or a
 * harness hook with no shell -- cannot rely on PATH.
 */

import { execFile } from "node:child_process";
import { homedir } from "node:os";
import { join } from "node:path";
import { promisify } from "node:util";
import { readProjectIndex, renderProjectCatalog } from "./fallback.ts";

const run = promisify(execFile);

// Where the `scripts` stow package puts it. An unstowed machine simply has
// no knowledge, which every caller here treats as "nothing configured".
const CLI = join(process.env.HOME || homedir(), "bin", "agent-knowledge");

// A knowledge lookup runs before the first turn, so it must not be what makes a
// session feel slow. Reads are small and local; a hang means something is wrong.
const TIMEOUT_MS = 10_000;

export interface BundleSummary {
	id: string;
	name: string;
	description: string;
}

export interface ResolveResult {
	catalog: string | null;
	bundles: BundleSummary[];
	diagnostics: { code: string; bundle_id: string | null; message: string }[];
}

export interface ReadResult {
	bundle_id: string | null;
	path: string | null;
	content: string | null;
	fragment: string | null;
	error: string | null;
}

export interface StatusResult {
	config_dir: string;
	bundles: { id: string; active: boolean; reason: string; path: string }[];
	diagnostics: { code: string; bundle_id: string | null; message: string }[];
}

/**
 * Run one CLI operation in `cwd` and parse its JSON payload.
 *
 * Returns undefined when the CLI is absent or unusable rather than throwing: a
 * machine that has not stowed it, or a broken install, must not break the
 * session that called us. A refused read is *not* this case -- the CLI exits 1
 * but still prints a payload naming the reason, which is parsed and returned.
 */
async function invoke<T>(args: string[], cwd: string): Promise<T | undefined> {
	try {
		// Windows does not execute extensionless shebang scripts through CreateProcess.
		// The launcher is Python, so invoke it through the interpreter there.
		const command = process.platform === "win32" ? "python" : CLI;
		const argv = process.platform === "win32" ? [CLI, ...args] : args;
		const { stdout } = await run(command, argv, { cwd, timeout: TIMEOUT_MS });
		return JSON.parse(stdout) as T;
	} catch (error) {
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

/**
 * Which bundles apply in `cwd`, and the catalog to disclose for them.
 *
 * `withProject: false` keeps the configured bundles but withholds the discovered
 * project one, for a caller whose own trust decision says the repository's
 * content should not be read yet. `trusted` reports that same decision to the
 * no-CLI path, which has no allowlist of its own to consult: without the CLI the
 * harness's trust is the only gate on reading repository-authored content, so it
 * is required rather than defaulted.
 */
export async function resolve(
	cwd: string,
	options: { withProject?: boolean; trusted?: boolean } = {},
): Promise<ResolveResult | undefined> {
	const args = ["resolve"];
	if (options.withProject === false) args.push("--no-project");
	const fromCli = await invoke<ResolveResult>(args, cwd);
	if (fromCli) return fromCli;

	if (options.withProject === false || options.trusted !== true)
		return undefined;
	const index = await readProjectIndex(cwd);
	if (!index) return undefined;
	return {
		catalog: renderProjectCatalog(index),
		bundles: [
			{
				id: "project",
				name: "Project knowledge",
				description: "References for the current project",
			},
		],
		diagnostics: [],
	};
}

/** One document from an active bundle, or a result carrying `error`. */
export function read(
	cwd: string,
	bundle: string,
	target: string,
	source?: string,
): Promise<ReadResult | undefined> {
	const args = ["read", "--bundle", bundle, "--target", target];
	if (source) args.push("--source", source);
	return invoke<ReadResult>(args, cwd);
}

/** The local status report. Names paths, so it is for the user, not the model. */
export function status(cwd: string): Promise<StatusResult | undefined> {
	return invoke<StatusResult>(["status"], cwd);
}
