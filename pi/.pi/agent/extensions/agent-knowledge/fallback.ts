/**
 * Reading a project bundle with no executable installed.
 *
 * A project bundle is Markdown committed inside the repo, so nothing but a file
 * read stands between an agent and its index. The CLI is what adds *structure* on
 * top: bundles configured outside the workspace, an allowlist deciding which
 * projects count, ordering across several bundles, constrained concept reads. All
 * of that is optional; the index is not.
 *
 * So this exists to make the extension useful on a machine that has never stowed
 * this repo -- clone, enable the extension, and a project's own knowledge shows
 * up. `resolver.ts` prefers the CLI whenever it answers.
 *
 * Deliberately narrow. It reads exactly one file at exactly one path, and refuses
 * anything it cannot verify, because every check the CLI performs would otherwise
 * have to be reimplemented here in a second language.
 */

import { execFile } from "node:child_process";
import { lstatSync, readFileSync, realpathSync } from "node:fs";
import { join, relative } from "node:path";
import { promisify } from "node:util";
import { BEGIN_MARKER, END_MARKER, newFence, PREAMBLE } from "./framing.ts";

const run = promisify(execFile);

const PROJECT_DIR = "agents-knowledge";
const INDEX = "index.md";
const SUPPORTED_VERSION = "0.2";

// Mirrors okf.MAX_INDEX_BYTES. An index is a catalog; anything this size is not
// one, and reading it would cost the context the bundle exists to save.
const MAX_INDEX_BYTES = 256 * 1024;

// Matched as text, not parsed as YAML: the marker must be the *string* "0.2",
// and a YAML load would accept the float 0.2 as equal.
const VERSION = /^okf_version:\s*"([^"]*)"\s*$/m;
const FRONTMATTER = /^---\r?\n([\s\S]*?)\r?\n---\r?(?:\n|$)/;

/**
 * The current worktree root, or the directory itself outside git.
 *
 * `--show-toplevel` reports the worktree containing `cwd` rather than the
 * repository's primary checkout, which is what keeps a feature worktree reading
 * its own branch's knowledge.
 */
async function projectRoot(cwd: string): Promise<string> {
	try {
		const { stdout } = await run("git", ["rev-parse", "--show-toplevel"], {
			cwd,
			timeout: 5_000,
		});
		return stdout.trim() || cwd;
	} catch {
		return cwd;
	}
}

/** Whether any entry from `path` up to `root` is a symlink. */
function hasSymlink(root: string, path: string): boolean {
	let current = path;
	while (current !== root && current.startsWith(root)) {
		if (lstatSync(current, { throwIfNoEntry: false })?.isSymbolicLink())
			return true;
		const parent = join(current, "..");
		if (parent === current) break;
		current = parent;
	}
	return false;
}

/**
 * The project bundle's root index text, or undefined when there is not one.
 *
 * Undefined covers every "nothing usable here" case, because callers treat them
 * identically: no bundle, no marker, an unreadable or oversized file, or a
 * symlink. A repository-controlled symlink is refused rather than followed --
 * `agents-knowledge` is content the repo can author, so it must not be able to
 * redirect a read outside the worktree.
 */
export async function readProjectIndex(
	cwd: string,
): Promise<string | undefined> {
	const root = await projectRoot(cwd);
	const bundle = join(root, PROJECT_DIR);
	const index = join(bundle, INDEX);

	try {
		if (hasSymlink(root, index)) return undefined;
		const stat = lstatSync(index, { throwIfNoEntry: false });
		if (!stat?.isFile() || stat.size > MAX_INDEX_BYTES) return undefined;
		// Belt and braces: refuse anything that resolves outside the worktree.
		if (relative(realpathSync(root), realpathSync(index)).startsWith("..")) {
			return undefined;
		}

		const text = readFileSync(index, "utf8");
		const frontmatter = FRONTMATTER.exec(text);
		if (!frontmatter) return undefined;
		const version = VERSION.exec(frontmatter[1] ?? "");
		return version?.[1] === SUPPORTED_VERSION ? text : undefined;
	} catch {
		return undefined;
	}
}

/**
 * A catalog for the project bundle alone, framed as the CLI frames one.
 *
 * The wording and fence come from `framing.ts`, shared with the CLI's Python so
 * the two cannot drift: the delimiter is the only structural control over
 * untrusted index text, and a second copy of it would be a second thing to keep
 * right.
 */
export function renderProjectCatalog(indexText: string): string {
	const fence = newFence();
	return [
		PREAMBLE.replace("{fence}", fence),
		"\n### Project knowledge (`project`)\n",
		"References for the current project\n\n",
		`${BEGIN_MARKER} project ${fence}\n`,
		`${indexText.trimEnd()}\n`,
		`${END_MARKER} project ${fence}\n`,
	].join("");
}
