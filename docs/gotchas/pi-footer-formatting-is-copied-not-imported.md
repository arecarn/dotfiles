# Changing one pi footer segment means reproducing the whole footer, and the copy silently ages

Pi's footer is a single component. An extension gets two hooks and neither edits a
segment: `ctx.ui.setStatus()` only appends a third line, leaving the segment it
was meant to replace still on screen, and `ctx.ui.setFooter()` replaces
everything. So "show context usage differently" costs a full reproduction of the
pwd line, `↑↓RW`, cache hit rate, cost, the `(sub)` and `xp` markers, the
right-aligned model with its provider prefix and thinking level, the dim
handling, the truncation, and the extension-status line.

That reproduction cannot import what it reproduces. `formatTokens`,
`formatCwdForFooter`, `createUsageTotals`, `addUsageToTotals`, and
`areExperimentalFeaturesEnabled` all live in the package but are **not** exported
from its entry point, so a custom footer copies them:

```
dist/modes/interactive/components/footer.js   # formatTokens, formatCwdForFooter
dist/core/usage-totals.js                     # createUsageTotals, addUsageToTotals
dist/core/experimental.js                     # PI_EXPERIMENTAL === "1"
```

Nothing warns when pi changes them. The footer keeps rendering, just no longer
like pi's -- a new segment upstream never appears, a changed token threshold
silently disagrees. `pi/.pi/agent/extensions/context-gauge-footer.ts` is this
repo's copy; diff it against the two files above after a pi upgrade.

Two details are not reachable at all rather than merely uncopied:

- **`(auto)`** comes from `session.autoCompactionEnabled`, a getter on
  `AgentSession`, which is absent from `ExtensionContext`. The nearest substitute
  is `SettingsManager.create(cwd).getCompactionEnabled()`, which is right at
  startup and stale after a mid-session toggle in `/settings`.
- **`(sub)`** comes from `ModelRuntime.isUsingSubscription()`, also unreachable.
  `ctx.modelRegistry` exposes `isUsingOAuth(model)` and `getProvider()`, so the
  same answer is `isUsingOAuth(model) && provider.auth.oauth.isSubscription`,
  plus pi's own special case for `kimi-coding` (subscription-backed while
  authenticating by API key).

A third-party footer package (`@pi-vault/pi-status`, `@smoose/pi-footer`,
`pi-powerline-footer`) pays the same tax; every one reimplements this, so
adopting one trades drift against pi for drift against its config schema.

**Confirmed:** 2026-09-06 against pi 0.84.3, by grepping `dist/index.js` for each
helper (absent) and reading `dist/modes/interactive/components/footer.js`,
`dist/core/extensions/types.d.ts`, and `dist/core/model-runtime.js`.
