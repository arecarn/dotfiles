---
name: goal-orchestrator
description: Use when running a user-started /goal that spans many steps and sub-agents over a long session — a multi-stream campaign (authoring, review, verification, integration) too large for one agent to hold in context. Not for a single small task one agent can just do.
---

# Goal Orchestrator

Running a long campaign (tens to hundreds of sub-agent dispatches) as an
orchestrator whose own context stays small and whose judgement stays
independent of the agents doing the work.

**Not for:** a task one agent can finish directly. Dispatching a single
helper for one step is normal delegation, not this skill — reach for it when
the work has multiple streams, a review loop, or will outlast one context
window.

## Settle scope before orchestrating

Before dispatching anything, grill the user (see `mattpocock-skills:grilling`)
until the campaign is settled, including:

- Scope (in/out), the end goals, and a measure of done for each stream.
- The workflow per stream (e.g. author -> independent review lenses ->
  validation, and the round cap).
- Which environments or resources are used, and in what order.
- The model split between orchestrator and sub-agents.
- Where work lives and how it's integrated (separate working copies or
  equivalent, one integration owner).
- What may run without asking versus what needs the user's approval each
  time (shared resources, outward-facing actions).
- How results are reported back (state table, report files).

Write the resulting answers into the goal text, the dispatch prompts, and the
state table as a "done when" per stream. Grill again whenever scope changes
mid-campaign. Orchestration starts only after the user confirms.

## The one rule

**The orchestrator plans, dispatches, verifies, and reports. It never writes,
reviews, or runs anything itself.** Every line of output, every test run,
every review comment comes from a sub-agent's report file, not from the
orchestrator's own hands. The orchestrator's only outputs are: a dispatch
prompt, a short state table, a question to the user, or a handoff.

This is what keeps the orchestrator's judgement independent — it can tell a
real pass from a report that merely claims one, because it never produced the
thing being checked.

## Running state table

Keep a short table, updated after every dispatch or report, not a narrative
log:

| Stream | Agent | Location | Done when | Status | Last verified |
|---|---|---|---|---|---|
| stream-a | author-a | copy A, version abc1234 | tests pass | review round 2 | version abc1234 confirmed directly |
| stream-b | validator-b | copy B | user-named check passes | waiting on that check | - |

Surface decisions to the user as this table plus the specific question, not as
a replay of agent chatter.

## Writing a dispatch prompt

Sub-agents don't inherit this conversation — paste every hard rule into every
prompt, not a reference to "the rules above." A dispatch prompt states:

- **Role**: what this agent is for, in one line.
- **Exact location and starting version**: where it works and what state it
  starts from. Never "the usual place."
- **File ownership**: the narrow set of files/areas it owns, and an explicit
  "do not touch" list for everything else. One writer per file (see Isolation
  below).
- **Inputs**: by path, not pasted inline — a stale paste drifts from the file.
- **Definition of done**: a checkable condition, not "make it good."
- **Verification commands**: the exact commands it must run and show output
  for, not "make sure it works."
- **Version-control rules, if any**: how to record the change, what never to
  touch (the shared mainline, another stream's work, shared config).
- **Output file path**: where it writes its report — findings, a draft, a
  diff — never only in chat.
- **Report instruction, verbatim**: "report back briefly with what you
  produced and where."

### Template

```
Role: <one line>
Location: <path>  Starting version: <ref/id>
You own: <files/areas>. Do not touch: <files/areas/other streams>.
Inputs: <path>, <path>
Definition of done: <checkable condition>
Verify with: <exact commands>
Version control: <rules, if any>, never touch <shared mainline/other streams>
Write your report to: <path>
Report back briefly with what you produced and where.
```

## Isolation

- **One writer per file or area.** Two agents editing the same thing race;
  split by file or area, not by task, when something would otherwise have
  two owners.
- **An isolated working copy per stream.** Each stream gets its own copy of
  the work (e.g. a worktree, a sandbox, a scratch directory) so one agent's
  half-finished edit never shows up in another's diff.
- **One place, one owner, for merging.** A dedicated location, owned by one
  integrator agent, is where streams combine. No stream merges another
  stream's work itself.
- **Throwaway copies for one-off runs.** A one-off build, test, or check gets
  its own disposable copy, pinned to the version under test. Clean these up
  when the run finishes — a pile of stale copies is how the orchestrator
  loses track of which version is actually live.

## Review loop

- **Author self-review is not independent review.** It is labelled as such in
  the report, never passed off as a second opinion.
- **Two independent lenses, by agents who didn't write the change**: one
  against the requirement (fidelity/completeness), one against the existing
  conventions (style/reuse/fit). Different concerns catch different defects;
  one reviewer wearing both hats catches fewer of either.
- **Cap fix rounds** (e.g. three). A change that still fails review after the
  cap is a signal to escalate to the user, not to keep iterating silently.
- **Done is what the user defined it to be.** A stream is finished when it
  meets the measure of done agreed at the start (a passing review, tests, a
  run, a check the user named), and you have verified that result yourself.
  A miss sends it back, not forward.
- **Reviewers write findings to a file.** A chat message is not a review; it
  disappears from the record the orchestrator checks.
- **Accept only written reviews you yourself dispatched.** Sub-agents
  sometimes message each other directly and one claims the other "approved
  it" — that claim is not evidence until the orchestrator reads the review
  file from the reviewer it dispatched.

## Verify every report yourself before accepting it

Never accept "passed," "pre-existing," or "unrelated" on a sub-agent's word.
Check it:

- The history of the thing in question — yourself, not a report about it. A
  defect reported as "pre-existing" is often one just introduced by a merge
  or an edit nobody traced back.
- Re-run the cheap gates (lint, unit tests, a fast consistency check) rather
  than trusting a pasted "all green."
- Read the report file the agent wrote, not just the chat summary of it.

Watch for two specific failure shapes, not just wrong answers: a **vacuous
pass** (a test that can't fail reported as passing), and an **assertion
weakened to pass** (a check loosened until the real bug slips through it).
Both read exactly like success in the chat summary.

## Outward-facing prose

Descriptions, ticket text, review replies — anything a human outside the
campaign will read. A sub-agent drafts it to a file. The orchestrator shows
the user the complete, verbatim text and waits for an explicit yes before
anything is posted. Never paraphrase the draft back to the user as a summary
— a summary isn't reviewable.

## Hygiene

- **Stop finished agents that keep emitting "waiting" notices.** A background
  agent idling after its work is done is noise, not progress.
- **Summarize to the user in short tables**, not prose transcripts.
- **Don't announce progress you haven't verified.** "Done" belongs after the
  check in Verify every report yourself, not before it.

## Cost and model choice

The orchestrator can run on a stronger model while sub-agents run on a cheaper
one, if that's what the user wants — follow the user's instruction on model
choice rather than defaulting either way.

## Handoffs

When context grows long, write a handoff and start a fresh orchestrator rather
than continuing in a context that's losing track of its own state. A handoff
captures:

- The state table as it stands.
- Every in-flight agent and how to check on it (its name/id, what it's
  working on, where its report will land).
- Every approval the user gave, quoted verbatim, not re-derived from memory.
- The remaining work, in the same shape as the original plan.
- Known traps hit so far, so the next orchestrator doesn't rediscover them.
