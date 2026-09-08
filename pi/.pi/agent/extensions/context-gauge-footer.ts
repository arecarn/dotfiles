/**
 * Pi's footer with the context segment led by a single-cell fill gauge.
 *
 * Pi shows context usage as `37.2%/200k (auto)`. This replaces the number with
 * `▃37%/200k (auto)`: the gauge is what a glance reads, the denominator stays
 * because a gauge cannot say how big the window is, and that varies from 200k to
 * 1M across models. Colour bands match claude-code/.claude/statusline.py so the
 * same fill means the same urgency in both harnesses -- deliberately earlier
 * than pi's own 70/90, since the cost of compacting early is nil.
 *
 * Everything else is pi's own footer, reproduced. Pi offers no hook to change
 * one segment: `setStatus` only appends a third line, leaving the number it is
 * meant to replace in place, so `setFooter` and a full reproduction is the only
 * route. Pi exports none of the formatting this needs (`formatTokens`,
 * `formatCwdForFooter`, its usage totals), hence the copies below -- see
 * docs/gotchas/pi-footer-formatting-is-copied-not-imported.md for what drifts
 * on a pi upgrade and how to re-check it.
 */

import { isAbsolute, relative, resolve, sep } from "node:path";
import type { AssistantMessage, Usage } from "@earendil-works/pi-ai";
import {
	type ExtensionAPI,
	SettingsManager,
} from "@earendil-works/pi-coding-agent";
import { truncateToWidth, visibleWidth } from "@earendil-works/pi-tui";

/** Percentages at which the gauge changes colour. Keep in step with statusline.py. */
const WARN_PERCENT = 50;
const DANGER_PERCENT = 75;

/** One glyph per eighth. Index 0 is a space, so an empty gauge occupies its cell. */
const GAUGE_LEVELS = " ▁▂▃▄▅▆▇█";

/** Minimum columns kept between the stats and the right-aligned model. */
const MIN_PADDING = 2;

/**
 * The gauge glyph for a percentage, clamped to 0-100.
 *
 * Rounds to the nearest eighth, but never down to the empty glyph while any
 * context is in use: at 1% an empty cell would read as an empty window.
 */
export function contextGauge(percent: number): string {
	const clamped = Math.max(0, Math.min(100, percent));
	const maxLevel = GAUGE_LEVELS.length - 1;
	let level = Math.round((clamped / 100) * maxLevel);
	if (clamped > 0) level = Math.max(1, level);
	return GAUGE_LEVELS.charAt(level);
}

/**
 * The context segment's text: gauge, integer percent, window size, auto marker.
 *
 * `percent` is null while pi cannot know it -- after a compaction, until the
 * next assistant response reports usage. That renders as `?` with no gauge,
 * because the empty glyph would claim an empty window rather than an unknown
 * one. Percent is integer where pi uses one decimal: beside a gauge the decimal
 * is noise, and it matches the Claude line.
 */
export function formatContextSegment(
	percent: number | null,
	contextWindow: number,
	autoCompact: boolean,
): string {
	const auto = autoCompact ? " (auto)" : "";
	const window = formatTokens(contextWindow);
	if (percent === null) return `?/${window}${auto}`;
	return `${contextGauge(percent)}${Math.round(percent)}%/${window}${auto}`;
}

/**
 * The theme colour for a context percentage, or undefined to leave it unstyled.
 *
 * An unknown percent is unstyled rather than green: nothing is being asserted.
 */
export function contextColour(
	percent: number | null,
): "error" | "warning" | "success" | undefined {
	if (percent === null) return undefined;
	if (percent >= DANGER_PERCENT) return "error";
	if (percent >= WARN_PERCENT) return "warning";
	return "success";
}

/** Compact token counts, as pi's footer formats them. */
export function formatTokens(count: number): string {
	if (count < 1000) return count.toString();
	if (count < 10000) return `${(count / 1000).toFixed(1)}k`;
	if (count < 1000000) return `${Math.round(count / 1000)}k`;
	if (count < 10000000) return `${(count / 1000000).toFixed(1)}M`;
	return `${Math.round(count / 1000000)}M`;
}

/** Replace a leading home directory with `~`, leaving paths outside it whole. */
export function formatCwdForFooter(
	cwd: string,
	home: string | undefined,
): string {
	if (!home) return cwd;
	const resolvedCwd = resolve(cwd);
	const resolvedHome = resolve(home);
	const relativeToHome = relative(resolvedHome, resolvedCwd);
	const isInsideHome =
		relativeToHome === "" ||
		(relativeToHome !== ".." &&
			!relativeToHome.startsWith(`..${sep}`) &&
			!isAbsolute(relativeToHome));
	if (!isInsideHome) return cwd;
	return relativeToHome === "" ? "~" : `~${sep}${relativeToHome}`;
}

/** Collapse control characters so one extension's status cannot break the line. */
function sanitizeStatusText(text: string): string {
	return text
		.replace(/[\r\n\t]/g, " ")
		.replace(/ +/g, " ")
		.trim();
}

interface UsageTotals {
	input: number;
	output: number;
	cacheRead: number;
	cacheWrite: number;
	cost: number;
}

function addUsage(totals: UsageTotals, usage: Usage): void {
	totals.input += usage.input;
	totals.output += usage.output;
	totals.cacheRead += usage.cacheRead;
	totals.cacheWrite += usage.cacheWrite;
	totals.cost += usage.cost.total;
}

export default function contextGaugeFooter(pi: ExtensionAPI): void {
	pi.on("session_start", (_event, ctx) => {
		// setFooter is a no-op outside the TUI, and SettingsManager would read
		// files for nothing in print and json modes.
		if (ctx.mode !== "tui") return;

		// Pi prints "(auto)" from session.autoCompactionEnabled, a getter on
		// AgentSession that extensions never receive. The setting behind it is
		// readable, so this agrees with pi except after a mid-session toggle in
		// /settings, where it stays at the startup value until pi restarts.
		let autoCompact = true;
		try {
			autoCompact = SettingsManager.create(ctx.cwd).getCompactionEnabled();
		} catch {
			// A footer that throws takes the whole TUI with it; assume pi's default.
		}

		ctx.ui.setFooter((tui, theme, footerData) => {
			const unsubscribe = footerData.onBranchChange(() => tui.requestRender());

			return {
				dispose: unsubscribe,
				invalidate() {},
				render(width: number): string[] {
					// Session-wide totals, which include turns compaction has since
					// dropped from the model's context. Deliberately not the same
					// question as the context gauge beside them.
					const totals: UsageTotals = {
						input: 0,
						output: 0,
						cacheRead: 0,
						cacheWrite: 0,
						cost: 0,
					};
					let latestCacheHitRate: number | undefined;
					for (const entry of ctx.sessionManager.getEntries()) {
						if (
							entry.type === "message" &&
							entry.message.role === "assistant"
						) {
							const message = entry.message as AssistantMessage;
							addUsage(totals, message.usage);
							// Overwritten each time, so this ends on the newest response.
							const prompt =
								message.usage.input +
								message.usage.cacheRead +
								message.usage.cacheWrite;
							latestCacheHitRate =
								prompt > 0
									? (message.usage.cacheRead / prompt) * 100
									: undefined;
						} else if (
							entry.type === "message" &&
							entry.message.role === "toolResult" &&
							entry.message.usage
						) {
							addUsage(totals, entry.message.usage);
						} else if (
							(entry.type === "branch_summary" ||
								entry.type === "compaction") &&
							entry.usage
						) {
							addUsage(totals, entry.usage);
						}
					}

					const contextUsage = ctx.getContextUsage();
					const contextWindow =
						contextUsage?.contextWindow ?? ctx.model?.contextWindow ?? 0;
					const percent = contextUsage?.percent ?? null;

					let pwd = formatCwdForFooter(
						ctx.sessionManager.getCwd(),
						process.env.HOME || process.env.USERPROFILE,
					);
					const branch = footerData.getGitBranch();
					if (branch) pwd = `${pwd} (${branch})`;
					const sessionName = ctx.sessionManager.getSessionName();
					if (sessionName) pwd = `${pwd} • ${sessionName}`;

					const statsParts: string[] = [];
					if (totals.input) statsParts.push(`↑${formatTokens(totals.input)}`);
					if (totals.output) statsParts.push(`↓${formatTokens(totals.output)}`);
					if (totals.cacheRead)
						statsParts.push(`R${formatTokens(totals.cacheRead)}`);
					if (totals.cacheWrite)
						statsParts.push(`W${formatTokens(totals.cacheWrite)}`);
					if (
						(totals.cacheRead > 0 || totals.cacheWrite > 0) &&
						latestCacheHitRate !== undefined
					) {
						statsParts.push(`CH${latestCacheHitRate.toFixed(1)}%`);
					}

					// Kimi Coding bills against a subscription despite authenticating
					// with an API key, so pi special-cases it. Everything else is a
					// subscription when its OAuth method declares itself one.
					const model = ctx.model;
					const provider = model
						? ctx.modelRegistry.getProvider(model.provider)
						: undefined;
					const usingSubscription = model
						? model.provider === "kimi-coding" ||
							(ctx.modelRegistry.isUsingOAuth(model) &&
								provider?.auth?.oauth?.isSubscription === true)
						: false;
					if (totals.cost || usingSubscription) {
						statsParts.push(
							`$${totals.cost.toFixed(3)}${usingSubscription ? " (sub)" : ""}`,
						);
					}

					const contextText = formatContextSegment(
						percent,
						contextWindow,
						autoCompact,
					);
					const colour = contextColour(percent);
					statsParts.push(colour ? theme.fg(colour, contextText) : contextText);

					if (process.env.PI_EXPERIMENTAL === "1") {
						statsParts.push(
							`${theme.fg("dim", "•")} ${theme.bold(theme.fg("warning", "xp"))}`,
						);
					}

					let statsLeft = statsParts.join(" ");
					let statsLeftWidth = visibleWidth(statsLeft);
					if (statsLeftWidth > width) {
						statsLeft = truncateToWidth(statsLeft, width, "...");
						statsLeftWidth = visibleWidth(statsLeft);
					}

					const modelName = model?.id || "no-model";
					let rightWithoutProvider = modelName;
					if (model?.reasoning) {
						const level = pi.getThinkingLevel() || "off";
						rightWithoutProvider =
							level === "off"
								? `${modelName} • thinking off`
								: `${modelName} • ${level}`;
					}

					// The provider prefix is a nicety: it is dropped rather than
					// allowed to push the model name off the line.
					let right = rightWithoutProvider;
					if (footerData.getAvailableProviderCount() > 1 && model) {
						right = `(${model.provider}) ${rightWithoutProvider}`;
						if (statsLeftWidth + MIN_PADDING + visibleWidth(right) > width) {
							right = rightWithoutProvider;
						}
					}

					const rightWidth = visibleWidth(right);
					let statsLine: string;
					if (statsLeftWidth + MIN_PADDING + rightWidth <= width) {
						statsLine =
							statsLeft +
							" ".repeat(width - statsLeftWidth - rightWidth) +
							right;
					} else {
						const availableForRight = width - statsLeftWidth - MIN_PADDING;
						if (availableForRight > 0) {
							const truncated = truncateToWidth(right, availableForRight, "");
							statsLine =
								statsLeft +
								" ".repeat(
									Math.max(0, width - statsLeftWidth - visibleWidth(truncated)),
								) +
								truncated;
						} else {
							statsLine = statsLeft;
						}
					}

					// statsLeft carries the context segment's own colour, which ends in
					// a reset that would cancel an outer dim. Dim the two spans either
					// side of it separately instead of wrapping the whole line.
					const dimStatsLeft = theme.fg("dim", statsLeft);
					const dimRemainder = theme.fg(
						"dim",
						statsLine.slice(statsLeft.length),
					);
					const lines = [
						truncateToWidth(
							theme.fg("dim", pwd),
							width,
							theme.fg("dim", "..."),
						),
						dimStatsLeft + dimRemainder,
					];

					const statuses = footerData.getExtensionStatuses();
					if (statuses.size > 0) {
						const line = Array.from(statuses.entries())
							.sort(([a], [b]) => a.localeCompare(b))
							.map(([, text]) => sanitizeStatusText(text))
							.join(" ");
						lines.push(truncateToWidth(line, width, theme.fg("dim", "...")));
					}

					return lines;
				},
			};
		});
	});
}
