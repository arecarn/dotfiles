---
description: Walk through a list of items one at a time — present each with enough context to decide, offer numbered options plus custom input and a discuss-more escape, and act on decisions. Use when the user says "walk me through these", "/walkthrough", "one by one", "go through these individually", "let's take these one at a time", or when a response contains a list (features, actions, findings, options, tasks) the user wants to address item-by-item instead of all at once.
argument-hint: "[list source or topic] [--apply-as-you-go]"
---

# Walkthrough

Walk through a list of items individually. For each item, give the user enough
background to decide, then let them choose an option, write their own, or open a
discussion. Record decisions and act on them — usually in a batch at the end.

This is the interactive, item-at-a-time pattern used by plan mode and
`gsd-discuss-phase`, generalized to any list.

## When to use

Use this whenever a list deserves per-item attention rather than one blanket
response:

- A response produced a list of features, actions, findings, options, or tasks
- The user explicitly asks to go "one by one" / "one at a time" / "individually"
- A decision on each item is non-trivial and benefits from focused context

Do **not** use it for a list where a single bulk action is obviously correct, or
where the user already told you what to do with every item.

## Step 1 — Establish the list

Identify the items to walk through:

- **From conversation** — if a list was just produced (yours or the user's), use
  it. Restate it compactly so both sides agree on scope.
- **From a source** — if `$ARGUMENTS` names a file, ticket query, diff, or topic,
  gather the items first (read files, grep, run commands as needed).
- **Ambiguous** — if it's unclear what the items are, ask before starting.

Number the items and confirm the set before diving in. Note the total so the user
knows the length (e.g. "8 items").

## Step 2 — Set the decision-handling mode

Decide how decisions get applied. Default is **collect-then-apply**:

- **Collect-then-apply (default)** — record each decision as you go, take no
  action until the end, then apply the whole batch. Lets the user see the full
  picture before anything changes. Prefer this.
- **Apply-as-you-go** — act on each decision immediately before advancing. Use
  only when an item's action is isolated and reversible, or when acting on it
  unblocks the *next* item's context. Passing `--apply-as-you-go` forces this
  mode for the whole run.

When an item clearly suits apply-as-you-go (e.g. it must run before the next item
makes sense), surface that and ask whether to apply now or queue it. Otherwise
stay in collect mode silently.

## Step 3 — Present each item, one at a time

For the current item, show:

1. **Header** — `Item N of M: <short title>`
2. **Background** — enough to decide, sized to the item: what it is, why it
   matters, and any tradeoffs or constraints. Keep it tight; link to
   `file_path:line` where relevant. Don't dump the whole list's context — just
   this item's.
3. **Options** — suggested choices, *if you have any*. Suggestions are optional:
   for a pure review ("does this look right?"), present the item and invite
   feedback without inventing options.

### Presenting options

**Prefer using `AskUserQuestion` when available** (e.g. Claude Code's native tool).
It renders a cleaner picker than text lists. Use it whenever you have options to
present — the tool auto-injects "Other" for custom input.

For `AskUserQuestion`:
- Fill up to 3 explicit suggestion options + 1 "Discuss more" option (4 total)
- Do **not** add a separate "write your own" option — "Other" already covers custom input
- The tool auto-validates that one option is selected or "Other" text provided
- Handles all three escapes: pick option, provide custom input via "Other", or discuss

For contexts without `AskUserQuestion` (e.g. opencode), fall back to **text numbered
list**: background as prose, then suggested options numbered `1.`, `2.`, … in the body.
After the numbered suggestions include:

- a custom slot — "…or describe your own", and
- a discuss-more slot — "…or say *discuss* to talk it through".

Every item must offer the same three escapes: pick an option, provide custom input,
or discuss further.

## Step 4 — Handle the response

- **Picked an option / gave custom input** → record it as the decision for this
  item. In apply-as-you-go mode, act now; in collect mode, store and advance.
- **Discuss more** → go back and forth on *this item only*. Bring new context,
  answer questions, refine options. When the user signals they've decided, record
  the decision and advance. Don't move on until the item is resolved or explicitly
  deferred.
- **Skip / defer** → record as deferred and advance. Don't lose it — it shows up
  in the summary.

After recording, move to the next item. Show progress (`Item 4 of 8`).

## Step 5 — Apply and summarize

At the end:

- In **collect-then-apply** mode, replay the recorded decisions and apply them as
  a batch now. Confirm the batch first if any action is destructive or
  outward-facing. Use whatever tools the surrounding session allows to carry out
  each decision (edits, commands, ticket updates, etc.) — this skill orchestrates
  the walk-through; it doesn't restrict how decisions get executed.
- Show a final summary table:

  | # | Item | Decision | Status |
  |---|------|----------|--------|
  | 1 | …    | option B | applied |
  | 2 | …    | custom: … | applied |
  | 3 | …    | deferred | — |
  | 4 | …    | —        | not reviewed |

  Status values: `applied`, `deferred`, `not reviewed` (for items left when a run
  is abandoned early), `—` for anything with no action.

- List anything deferred or still needing attention.

## Notes

- Keep momentum: one item on screen at a time, minimal preamble, clear progress.
- Match background depth to stakes — a one-liner for an obvious item, a paragraph
  with tradeoffs for a consequential one.
- The user can always abandon the walk-through; respect "just do them all" or
  "stop" at any point, and mark unreviewed items accordingly in the summary.
