---
description: Walk through a list of items one at a time — present each with enough context to decide, offer numbered options plus custom input and a discuss-more escape, and act on decisions. Use when the user says "walk me through these", "/walkthrough", "one by one", "go through these individually", "let's take these one at a time", or when a response contains a list (features, actions, findings, options, tasks) the user wants to address item-by-item instead of all at once.
argument-hint: "[list source or topic] [--apply-as-you-go]"
model: haiku
---

# Walkthrough

Walk through a list one item at a time. Give enough context to decide, let the
user choose or discuss, review any resulting output, and act on approved
decisions.

Use this when each item deserves focused attention. Skip it when one bulk action
is clearly right or the user has already decided every item.

## 1. Establish the list

Get the items from the conversation or the source named in `$ARGUMENTS`. If the
scope is unclear, ask. Restate the numbered list compactly and give the total.

## 2. Suggest batching

Scan the list for items similar enough to decide the same way, or coupled
enough that deciding one determines the others. Propose grouping those into a
single decision point — for example, "items 3-5 all rename the same field;
review them together?" — and let the user accept, decline, or adjust the
grouping before walking through anything. Leave every other item at one item
per decision point. This is a suggestion, never automatic: don't merge items
just to move faster, and don't merge ones that differ in anything the decision
depends on.

## 3. Decide when to apply

Approved decisions are normally collected and applied together at the end. If
`--apply-as-you-go` was requested, apply each approved decision before moving
on. Ask about applying early only when an isolated, reversible action must
happen before the next decision point makes sense.

## 4. Present one item or batch

Show only the current decision point:

- `Item N of M: <short title>` — for a batch, `Items 3-5 of M: <shared title>`,
  where M counts decision points, not original list items
- enough background to decide, including important tradeoffs or constraints;
  for a batch, what the items share and anything that differs between them
- up to three useful choices when there are natural options

Always allow the user to choose a suggestion, provide a custom answer, or say
**discuss**. A pure review may simply invite feedback rather than inventing
options. Use a native question picker when available; otherwise use a numbered
list.

If the user says **discuss**, stay on this item, answer questions, and refine the
choices until they decide. Record skipped or deferred items and advance.

## 5. Review the result

If a decision produces no authored prose or concrete action, record it and
advance.

Otherwise, show one complete review of the proposed output:

- authored prose verbatim; for an edit to existing text, a unified diff in a
  `diff` block with enough surrounding lines to place each change, plus the
  full text when the edit amounts to a rewrite rather than a targeted change
- for an action, the affected values, file change, state transition, command
  effect, or equivalent result
- the impact, when it isn't obvious from the output alone: what else the
  change touches, who or what will see it, and whether it can be undone

Offer **Approve**, **Revise**, and **Discuss more**. Incorporate feedback and
present the complete revised review until the user explicitly approves it.

Record only approved output, against every item it covers when the decision was
made as a batch. Apply it now in apply-as-you-go mode or retain it for the final
batch, then continue with the next decision point.

## 6. Apply and summarize

Apply collected decisions as a batch. Approval normally authorizes this step;
confirm again only when an action is destructive or the relevant circumstances
have changed since approval.

Finish with a concise list of decisions and their status, one row per original
list item even when several shared a batched decision — name the batch
alongside it. Use a table only when it improves a long or complex summary.
Identify anything deferred or not reviewed.

Keep momentum throughout: minimal preamble, context matched to the stakes, and
one decision point on screen at a time. If the user says **stop** or **just do
them all**, respect it and summarize what remains.
