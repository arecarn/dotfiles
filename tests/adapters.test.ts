/**
 * Contract tests for the three harness adapters.
 *
 * The point of one shared CLI is that pi, Claude Code, and OpenCode cannot
 * disagree about which knowledge applies. That only holds if each adapter
 * actually asks the CLI and passes its answer through unchanged, so these run
 * the real adapters against real bundle fixtures and compare what each produces.
 *
 * The adapters resolve the CLI at `~/bin/agent-knowledge`, the stowed path. A
 * checkout under test has not necessarily been stowed, so the launcher is linked
 * into a temporary HOME and `homedir()` is pointed at it -- rather than guarding
 * on "is it installed?", which silently turns every assertion below into a test
 * of the not-installed path. The degradation path gets its own test instead.
 *
 * Node's own runner and type stripping, so this needs no dependency beyond the
 * toolchain `inv lint` already installs:
 *
 *     node --experimental-strip-types --test tests/adapters.test.ts
 */

import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import {
	mkdirSync,
	mkdtempSync,
	rmSync,
	symlinkSync,
	writeFileSync,
} from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { after, test } from "node:test";
import { fileURLToPath, pathToFileURL } from "node:url";

const REPO = join(dirname(fileURLToPath(import.meta.url)), "..");

const INDEX = `---\nokf_version: "0.2"\n---\n# Personal\n\n* [Ops](ops.md) - operations\n`;
const PROJECT_INDEX = `---\nokf_version: "0.2"\n---\n# Project\n\n* [Release](release.md) - shipping\n`;

const roots: string[] = [];

/** A HOME whose ~/bin/agent-knowledge is this checkout's launcher. */
function stubHome() {
	const home = mkdtempSync(join(tmpdir(), "agent-knowledge-home-"));
	roots.push(home);
	mkdirSync(join(home, "bin"), { recursive: true });
	symlinkSync(
		join(REPO, "agents", "bin", "agent-knowledge"),
		join(home, "bin", "agent-knowledge"),
	);
	return home;
}

/** One always-active bundle plus a project bundle in a git repo. */
function fixture() {
	const root = mkdtempSync(join(tmpdir(), "agent-knowledge-"));
	roots.push(root);

	// The bundle lives inside the config directory: a directory beside the
	// config file is a bundle, so nothing declares it.
	const config = join(root, "config");
	const bundle = join(config, "personal");
	mkdirSync(bundle, { recursive: true });
	writeFileSync(join(bundle, "index.md"), INDEX);
	writeFileSync(join(bundle, "ops.md"), "# Ops\n\nRun the thing.\n");

	const project = join(root, "projects", "repo");
	mkdirSync(join(project, "agents-knowledge"), { recursive: true });
	writeFileSync(join(project, "agents-knowledge", "index.md"), PROJECT_INDEX);
	execFileSync("git", ["init", "-q", "."], { cwd: project });

	return { root, bundle, project, config };
}

/**
 * Load an adapter with HOME and the config directory set for one call.
 *
 * The module reads `homedir()` at import time, so each case needs a fresh module
 * instance: a query string defeats the ESM cache without touching the source.
 */
async function adapter(path: string, home: string, config: string) {
	process.env.HOME = home;
	process.env.AGENT_KNOWLEDGE_CONFIG_DIR = config;
	const moduleUrl = pathToFileURL(join(REPO, path));
	moduleUrl.search = `v=${roots.length}-${Math.random()}`;
	return import(moduleUrl.href);
}

const PI = "pi/.pi/agent/extensions/agent-knowledge/resolver.ts";
const OPENCODE = "opencode/.config/opencode/plugins/agent-knowledge.ts";

const originalHome = process.env.HOME;

after(() => {
	process.env.HOME = originalHome;
	delete process.env.AGENT_KNOWLEDGE_CONFIG_DIR;
	for (const root of roots) rmSync(root, { recursive: true, force: true });
});

test("the pi adapter resolves configured and project bundles in order", async () => {
	const { config, project, bundle } = fixture();
	const pi = await adapter(PI, stubHome(), config);

	const result = await pi.resolve(project);

	assert.deepEqual(
		result?.bundles.map((b: { id: string }) => b.id),
		["personal", "project"],
	);
	assert.match(result.catalog ?? "", /operations/);
	assert.match(result.catalog ?? "", /shipping/);
	assert.ok(
		!(result.catalog ?? "").includes(bundle),
		"the catalog must not name a bundle's path",
	);
});

test("the pi adapter can withhold the project bundle", async () => {
	const { config, project } = fixture();
	const pi = await adapter(PI, stubHome(), config);

	const withheld = await pi.resolve(project, { withProject: false });

	assert.deepEqual(
		withheld?.bundles.map((b: { id: string }) => b.id),
		["personal"],
	);
});

test("the pi adapter reads a document and refuses an escape", async () => {
	const { config, root, project } = fixture();
	writeFileSync(join(root, "secret.md"), "secret\n");
	const pi = await adapter(PI, stubHome(), config);

	const ok = await pi.read(project, "personal", "ops.md");
	assert.equal(ok?.content, "# Ops\n\nRun the thing.\n");

	const refused = await pi.read(project, "personal", "../secret.md");
	assert.equal(refused?.content, null);
	assert.equal(refused?.error, "path_escape");
});

test("status names paths for the user", async () => {
	const { config, project, bundle } = fixture();
	const pi = await adapter(PI, stubHome(), config);

	const report = await pi.status(project);

	assert.ok(report?.bundles.some((b: { path: string }) => b.path === bundle));
});

test("a broken configuration yields diagnostics and no catalog", async () => {
	const { root } = fixture();
	const broken = join(root, "broken");
	mkdirSync(broken, { recursive: true });
	writeFileSync(join(broken, "config.yaml"), "version: 99\n");
	const pi = await adapter(PI, stubHome(), broken);

	const result = await pi.resolve(root);

	assert.equal(result?.catalog, null);
	assert.ok(
		result?.diagnostics.some(
			(d: { code: string }) => d.code === "config_error",
		),
	);
});

test("an absent CLI is no knowledge, not an error", async () => {
	const { config, project } = fixture();
	const empty = mkdtempSync(join(tmpdir(), "agent-knowledge-nohome-"));
	roots.push(empty);
	const pi = await adapter(PI, empty, config);

	assert.equal(await pi.resolve(project), undefined);
	assert.equal(await pi.status(project), undefined);
	assert.equal(await pi.read(project, "personal", "ops.md"), undefined);
});

test("the OpenCode plugin adds exactly one catalog per request and caches it", async () => {
	const { config, project } = fixture();
	const mod = await adapter(OPENCODE, stubHome(), config);
	const plugin = await mod.AgentKnowledge({
		directory: project,
		worktree: project,
	});

	const first = { system: [] as string[] };
	const second = { system: [] as string[] };
	await plugin["experimental.chat.system.transform"](
		{ sessionID: "s1" },
		first,
	);
	await plugin["experimental.chat.system.transform"](
		{ sessionID: "s1" },
		second,
	);

	assert.equal(first.system.length, 1);
	assert.equal(second.system.length, 1, "each request gets exactly one copy");
	assert.equal(first.system[0], second.system[0], "cached, not re-read");
	assert.match(first.system[0] ?? "", /operations/);
});

test("the OpenCode plugin agrees with pi on which bundles apply", async () => {
	const { config, project } = fixture();
	const home = stubHome();

	const pi = await adapter(PI, home, config);
	const piCatalog = (await pi.resolve(project))?.catalog;

	const mod = await adapter(OPENCODE, home, config);
	const plugin = await mod.AgentKnowledge({
		directory: project,
		worktree: project,
	});
	const output = { system: [] as string[] };
	await plugin["experimental.chat.system.transform"](
		{ sessionID: "s1" },
		output,
	);

	// Fences carry a per-render nonce, so compare the bundle headings rather than
	// the whole text.
	const headings = (text: string) => text.match(/^### .*$/gm);
	assert.deepEqual(headings(output.system[0] ?? ""), headings(piCatalog ?? ""));
});

test("the OpenCode plugin exposes the same read refusals", async () => {
	const { config, project } = fixture();
	const mod = await adapter(OPENCODE, stubHome(), config);
	const plugin = await mod.AgentKnowledge({
		directory: project,
		worktree: project,
	});
	const read = plugin.tool.knowledge_read.execute;

	assert.match(
		await read({ bundle: "project", target: "index.md" }),
		/Project/,
	);
	assert.match(
		await read({ bundle: "project", target: "../../secret.md" }),
		/Cannot read/,
	);
	assert.match(
		await read({ bundle: "nope", target: "index.md" }),
		/bundle_inactive/,
	);
});

test("a symlinked project bundle is refused through the adapters too", async () => {
	const { config, root } = fixture();

	const elsewhere = join(root, "elsewhere");
	mkdirSync(elsewhere, { recursive: true });
	writeFileSync(join(elsewhere, "index.md"), PROJECT_INDEX);

	const linked = join(root, "projects", "linked");
	mkdirSync(linked, { recursive: true });
	execFileSync("git", ["init", "-q", "."], { cwd: linked });
	symlinkSync(elsewhere, join(linked, "agents-knowledge"));

	const pi = await adapter(PI, stubHome(), config);
	const result = await pi.resolve(linked);

	assert.deepEqual(
		result?.bundles.map((b: { id: string }) => b.id),
		["personal"],
		"a repo-controlled symlink must not reach outside the worktree",
	);
});

test("without the CLI, pi still injects the project index", async () => {
	const { config, project } = fixture();
	const empty = mkdtempSync(join(tmpdir(), "agent-knowledge-nocli-"));
	roots.push(empty);
	const pi = await adapter(PI, empty, config);

	const result = await pi.resolve(project, { trusted: true });

	assert.deepEqual(
		result?.bundles.map((b: { id: string }) => b.id),
		["project"],
		"a project bundle is Markdown in the repo; it needs no executable",
	);
	assert.match(result.catalog ?? "", /shipping/);
});

test("the fallback withholds the project bundle when the harness distrusts it", async () => {
	const { config, project } = fixture();
	const empty = mkdtempSync(join(tmpdir(), "agent-knowledge-nocli-"));
	roots.push(empty);
	const pi = await adapter(PI, empty, config);

	assert.equal(await pi.resolve(project, { trusted: false }), undefined);
});

test("the fallback frames index text exactly as the CLI does", async () => {
	const { config, project } = fixture();
	const home = stubHome();

	const withCli = await (await adapter(PI, home, config)).resolve(project);
	const empty = mkdtempSync(join(tmpdir(), "agent-knowledge-nocli-"));
	roots.push(empty);
	const without = await (await adapter(PI, empty, config)).resolve(project, {
		trusted: true,
	});

	// The framing is the one structural control on untrusted text, and it lives in
	// two languages. Compare every line, normalising the per-render nonce and
	// dropping only the bundle the no-CLI path cannot reach.
	// Keep every line except the configured bundle's section, which the no-CLI
	// path cannot reach: from its "### Personal" heading to the next heading.
	const shape = (text: string) => {
		const kept: string[] = [];
		let skipping = false;
		for (const line of text.replace(/[0-9a-f]{16}/g, "<fence>").split("\n")) {
			if (line.startsWith("### ")) skipping = line.startsWith("### Personal");
			if (!skipping) kept.push(line);
		}
		return kept;
	};

	assert.deepEqual(
		shape(without?.catalog ?? ""),
		shape(withCli?.catalog ?? ""),
	);
});

test("the fallback refuses a symlinked project bundle", async () => {
	const { config, root } = fixture();
	const elsewhere = join(root, "outside");
	mkdirSync(elsewhere, { recursive: true });
	writeFileSync(join(elsewhere, "index.md"), PROJECT_INDEX);

	const linked = join(root, "projects", "sneaky");
	mkdirSync(linked, { recursive: true });
	symlinkSync(elsewhere, join(linked, "agents-knowledge"));

	const empty = mkdtempSync(join(tmpdir(), "agent-knowledge-nocli-"));
	roots.push(empty);
	const pi = await adapter(PI, empty, config);

	assert.equal(await pi.resolve(linked, { trusted: true }), undefined);
});

test("the fallback ignores a directory without the version marker", async () => {
	const { config, root } = fixture();
	const plain = join(root, "projects", "plain");
	mkdirSync(join(plain, "agents-knowledge"), { recursive: true });
	writeFileSync(join(plain, "agents-knowledge", "index.md"), "# just docs\n");

	const empty = mkdtempSync(join(tmpdir(), "agent-knowledge-nocli-"));
	roots.push(empty);
	const pi = await adapter(PI, empty, config);

	assert.equal(await pi.resolve(plain, { trusted: true }), undefined);
});
