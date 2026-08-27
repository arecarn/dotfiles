# A pi extension sees context in branch history that the model can no longer read

An extension that injects context once per session, then checks "have I already
injected?" with `ctx.sessionManager.getEntries()` or `getBranch()`, stops
re-injecting after a compaction — and the model has no memory of the content.

Compaction rebuilds model context from a summary plus the retained tail, but it
does **not** delete the earlier entries from the session's branch. So a
`custom_message` entry added before compaction is still in `getBranch()` forever,
while the model stops seeing it the moment compaction lands. Both are true at the
same time, which is why the bug looks like the extension "just stopped working".

`buildContextEntries()` is the one that answers the question actually being
asked. It walks the branch applying compaction, so it reports what the model can
read right now:

```typescript
for (const entry of ctx.sessionManager.buildContextEntries()) {
  if (entry.type === "custom_message" && entry.customType === MINE) return true;
}
```

The failure is silent in both directions: use `buildContextEntries()` and a
resumed session correctly skips re-injection; use `getBranch()` and a compacted
session silently loses the context with no error anywhere.

Applies to any once-per-session injection, not just knowledge catalogs — a todo
list, a project brief, a set of rules.

**Confirmed:** 2026-08-27 against pi 0.84.3, reading `docs/compaction.md`
("`buildContextEntries()` walks from the current leaf to the root, producing the
active entry list while honoring compaction") and `docs/session-format.md`.
