/**
 * State-change contract for the monitor registry's persistent UI indicator.
 *
 * Run with:
 *
 *     node --experimental-strip-types --test tests/monitor.test.ts
 */

import assert from "node:assert/strict";
import { test } from "node:test";
import type { ExtensionContext } from "@earendil-works/pi-coding-agent";
import {
	type Monitor,
	MonitorRegistry,
} from "../pi/.pi/agent/extensions/monitor/registry.ts";

const cwd = process.cwd();
const context = {} as ExtensionContext;

test("reports running and disarmed monitor counts", () => {
	const changes: Array<{ running: number; context?: ExtensionContext }> = [];
	const registry = new MonitorRegistry(
		() => {},
		(monitors, ctx) => {
			changes.push({
				running: monitors.filter((monitor) => monitor.status === "running")
					.length,
				context: ctx,
			});
		},
	);
	registry.noteContext(context);

	const monitor = registry.arm({ command: "sleep 60", cwd });
	registry.disarm(monitor.id);

	assert.deepEqual(changes, [
		{ running: 1, context },
		{ running: 0, context },
	]);
});

test("reports when a monitor completes without an explicit disarm", async () => {
	let resolveDone: (() => void) | undefined;
	const done = new Promise<void>((resolve) => {
		resolveDone = resolve;
	});
	const states: Monitor["status"][] = [];
	const registry = new MonitorRegistry(
		() => {},
		(monitors) => {
			const monitor = monitors[0];
			if (monitor === undefined) return;
			states.push(monitor.status);
			if (monitor.status === "done") resolveDone?.();
		},
	);

	registry.arm({ command: "printf 'finished\\n'", cwd });
	await Promise.race([
		done,
		new Promise<never>((_resolve, reject) => {
			setTimeout(() => reject(new Error("monitor did not complete")), 2000);
		}),
	]);

	assert.deepEqual(states, ["running", "done"]);
});
