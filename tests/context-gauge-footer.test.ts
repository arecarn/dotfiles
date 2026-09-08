/**
 * The context segment of pi's footer, replaced by a fill gauge.
 *
 * Only the pure formatting is covered. The render callback needs a live TUI,
 * theme, and footer data provider, so it is verified by hand against pi's own
 * footer.js instead.
 *
 * Run with:
 *
 *     node --experimental-strip-types --test tests/context-gauge-footer.test.ts
 */

import assert from "node:assert/strict";
import { sep } from "node:path";
import { test } from "node:test";
import {
	contextColour,
	contextGauge,
	formatContextSegment,
	formatCwdForFooter,
	formatTokens,
} from "../pi/.pi/agent/extensions/context-gauge-footer.ts";

test("gauge fills by eighths across the range", () => {
	assert.equal(contextGauge(0), " ");
	assert.equal(contextGauge(50), "▄");
	assert.equal(contextGauge(100), "█");
});

test("gauge never reads empty while any context is used", () => {
	// 1% rounds to level 0, which is the blank glyph -- indistinguishable from an
	// unused window. Every nonzero percent must show at least the lowest bar.
	assert.equal(contextGauge(1), "▁");
	assert.equal(contextGauge(6), "▁");
});

test("gauge clamps out-of-range percentages", () => {
	assert.equal(contextGauge(-5), " ");
	assert.equal(contextGauge(140), "█");
});

test("colour bands match the Claude status line at 50 and 75", () => {
	assert.equal(contextColour(0), "success");
	assert.equal(contextColour(49), "success");
	assert.equal(contextColour(50), "warning");
	assert.equal(contextColour(74), "warning");
	assert.equal(contextColour(75), "error");
	assert.equal(contextColour(100), "error");
});

test("an unknown percentage is left unstyled", () => {
	assert.equal(contextColour(null), undefined);
});

test("segment leads with the gauge and keeps the window size", () => {
	assert.equal(formatContextSegment(37.2, 200000, true), "▃37%/200k (auto)");
	assert.equal(formatContextSegment(37.2, 200000, false), "▃37%/200k");
});

test("segment shows no gauge when the percentage is unknown", () => {
	// Post-compaction, until the next response reports usage. A blank gauge cell
	// would claim an empty window rather than an unknown one.
	assert.equal(formatContextSegment(null, 200000, true), "?/200k (auto)");
	assert.equal(formatContextSegment(null, 1000000, false), "?/1.0M");
});

test("token counts keep pi's own thresholds and precision", () => {
	assert.equal(formatTokens(999), "999");
	assert.equal(formatTokens(1000), "1.0k");
	assert.equal(formatTokens(10000), "10k");
	assert.equal(formatTokens(200000), "200k");
	assert.equal(formatTokens(1000000), "1.0M");
	assert.equal(formatTokens(10000000), "10M");
});

test("paths under home collapse to ~, others stay absolute", () => {
	// Separator from node:path, as the formatter uses: pi joins with the platform's
	// own, so hardcoding "/" here passes on Linux and fails the Windows CI leg.
	assert.equal(
		formatCwdForFooter("/home/u/dotfiles", "/home/u"),
		`~${sep}dotfiles`,
	);
	assert.equal(formatCwdForFooter("/home/u", "/home/u"), "~");
	assert.equal(formatCwdForFooter("/etc", "/home/u"), "/etc");
	// A sibling whose name merely starts with home's is not inside it.
	assert.equal(formatCwdForFooter("/home/user2", "/home/u"), "/home/user2");
	assert.equal(formatCwdForFooter("/etc", undefined), "/etc");
});
