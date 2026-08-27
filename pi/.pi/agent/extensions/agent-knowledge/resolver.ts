/**
 * Talking to the `agent-knowledge` CLI.
 *
 * Bundle selection, OKF validation, and read safety all live in the CLI so that
 * pi, Claude Code, and OpenCode cannot drift apart on which knowledge applies
 * here. This module is only transport: spawn, parse, and translate a failure
 * into something the caller can render.
 *
 * The CLI is invoked by absolute path from ~/.local/bin, where stow puts it, so
 * a session started anywhere finds it without a PATH that includes it.
 */

import { execFile } from "node:child_process";
import { homedir } from "node:os";
import { join } from "node:path";
import { promisify } from "node:util";

const run = promisify(execFile);

// Where the `scripts` stow package puts it. An unstowed machine simply has
// no knowledge, which every caller here treats as "nothing configured".
const CLI = join(homedir(), "bin", "agent-knowledge");

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
	project_roots: string[];
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
		const { stdout } = await run(CLI, args, { cwd, timeout: TIMEOUT_MS });
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

/** Which bundles apply in `cwd`, and the catalog to disclose for them. */
export function resolve(cwd: string): Promise<ResolveResult | undefined> {
	return invoke<ResolveResult>(["resolve"], cwd);
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
