/**
 * The pure state-reading half of the pi superpowers-toggle extension.
 *
 * Only stateDir/isEnabled are covered. The context handler and registered
 * command need a live ExtensionAPI, so they are verified by hand against a
 * running pi session instead, matching context-gauge-footer.test.ts's split.
 *
 * Run with:
 *
 *     node --experimental-strip-types --test tests/superpowers-toggle.test.ts
 */

import assert from "node:assert/strict";
import { mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { test } from "node:test";
import {
	isEnabled,
	stateDir,
} from "../pi/.pi/agent/extensions/superpowers-toggle.ts";

test("an untouched state dir is enabled", () => {
	const dir = mkdtempSync(join(tmpdir(), "superpowers-toggle-"));
	try {
		assert.equal(isEnabled(dir), true);
	} finally {
		rmSync(dir, { recursive: true, force: true });
	}
});

test("a flag file containing off is disabled", () => {
	const dir = mkdtempSync(join(tmpdir(), "superpowers-toggle-"));
	try {
		writeFileSync(join(dir, "superpowers-bootstrap"), "off");
		assert.equal(isEnabled(dir), false);
	} finally {
		rmSync(dir, { recursive: true, force: true });
	}
});

test("a flag file containing anything else is enabled", () => {
	const dir = mkdtempSync(join(tmpdir(), "superpowers-toggle-"));
	try {
		writeFileSync(join(dir, "superpowers-bootstrap"), "on");
		assert.equal(isEnabled(dir), true);
	} finally {
		rmSync(dir, { recursive: true, force: true });
	}
});

test("stateDir prefers the env var override", () => {
	assert.equal(
		stateDir({ SUPERPOWERS_TOGGLE_STATE_DIR: "/tmp/custom" }),
		"/tmp/custom",
	);
});

test("stateDir falls back to XDG_STATE_HOME then HOME", () => {
	assert.equal(
		stateDir({ XDG_STATE_HOME: "/tmp/state" }),
		join("/tmp/state", "ai-skills"),
	);
});
