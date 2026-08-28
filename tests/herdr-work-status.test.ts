/**
 * Compact Herdr agent-row status for Pi-owned background work.
 *
 * Run with:
 *
 *     node --experimental-strip-types --test tests/herdr-work-status.test.ts
 */

import assert from "node:assert/strict";
import { test } from "node:test";
import {
	formatWorkStatus,
	WorkStatus,
} from "../pi/.pi/agent/extensions/herdr-work-status.ts";

test("formats only nonzero work counts in monitor, background, agent order", () => {
	assert.equal(
		formatWorkStatus({ monitors: 1, background: 2, agents: 3 }),
		"M1 B2 A3",
	);
	assert.equal(
		formatWorkStatus({ monitors: 0, background: 2, agents: 0 }),
		"B2",
	);
	assert.equal(
		formatWorkStatus({ monitors: 0, background: 0, agents: 0 }),
		undefined,
	);
});

test("publishes only when a count changes", () => {
	const published: Array<string | undefined> = [];
	const status = new WorkStatus((value) => published.push(value));

	status.set("monitors", 1);
	status.set("monitors", 1);
	status.set("agents", 2);
	status.set("monitors", 0);
	status.set("agents", 0);

	assert.deepEqual(published, ["M1", "M1 A2", "A2", undefined]);
});

test("normalizes invalid counts to zero", () => {
	const published: Array<string | undefined> = [];
	const status = new WorkStatus((value) => published.push(value));

	status.set("background", -1);
	status.set("background", Number.NaN);
	status.set("background", 1.8);

	assert.deepEqual(published, ["B1"]);
});
