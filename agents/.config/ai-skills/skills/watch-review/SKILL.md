---
name: watch-review
description: Watch a GitLab merge request or GitHub pull request for feedback that is relevant to you, in the background, without spending model tokens on polling.
disable-model-invocation: true
---

# Watch Review

`watch_review.py` polls a review and prints one compact batch per poll of new
human feedback relevant to the authenticated user. Each item includes its local
time as an ISO date with a readable clock time, such as `2026-08-27 at 2:32 PM
PDT`. It prints a terminal event and exits when the review is merged or closed
without merge. **The polling is plain Python: it costs no model tokens and
prints nothing while nothing changes.**

Relevance comes from API relationships and exact `@name` syntax, never from a
model. If the authenticated user authored the review, all other people's
feedback counts; otherwise only exact mentions of them and replies to their own
comments do.

`--as-reviewer` widens that to every other person's feedback, and adds a line
whenever the head commit moves. Use it when the authenticated user is the
review's principal reviewer rather than a commenter: they own threads they never
posted in, and a push obliges them to re-check what they already signed off, so
the default filter hides the work instead of surfacing it.

## Run it in the background

Take the review URL from the argument, or infer it from the current branch's MR
or PR. `--interval` is seconds, default 120.

```bash
python3 ~/.config/ai-skills/skills/watch-review/watch_review.py <review-url> [--interval 120] [--as-reviewer] [--output-format text|jsonl]
```

| Harness | Binding |
|---|---|
| pi | The `monitor` tool, armed with no `maxEvents` and `wake: true`. Run the command with `--output-format jsonl`, which gives the line-oriented monitor one event per logical notification. Unlimited because feedback arrives more than once; `wake: true` starts a turn as soon as a feedback batch arrives so it can be surfaced immediately. |
| Claude Code | Its `Monitor` background capability on the default text command. |
| anything else | Whatever runs a command detached and reports its output later. |

Authentication comes from `glab` and `gh`, so neither a token nor a host needs
passing. Self-hosted GitLab and GitHub Enterprise work from the URL's hostname.

### Pi JSON Lines contract

`--output-format jsonl` emits exactly one compact JSON object per physical
stdout line. A feedback object has `type: "feedback"`, `count`, and an `events`
array. Every event carries its provider `id`, original `timestamp`, `author`,
unaltered `body`, and `url`. JSON escaping keeps multiline bodies on that one
physical line without discarding their newlines.

A terminal object has `type: "terminal"`, `state` (`merged` or `closed`),
`message`, and the review `url`. The process exits immediately after writing it.
The default `text` format remains the readable direct-CLI interface.

## Assess each feedback batch

When a batch arrives, preserve each item's timestamp, author, original text, and
link, then assess the work it creates. Present the batch in this order:

1. State the most consequential classification and whether immediate action is
   needed.
2. For every item, assign exactly one classification: `blocking`, `action
   required`, `question`, `informational`, or `new commit`.
3. Give a concise rationale based on the feedback and a concrete next action.
   Use `None` when an informational item requires no action.

A `blocking` item says the review cannot proceed until something is resolved.
`action required` asks for a change or decision without explicitly blocking the
review. `question` asks for information. `informational` supplies context
without requesting work. `new commit` reports a moved head and requires the
principal reviewer to re-check affected conclusions.

Do not draft or post a reply unless the user asks. The watcher only reads; it
never replies, resolves, approves, or merges.

A terminal event is one of:

```text
Review merged
<review-url>
```

```text
Review closed without merge
<review-url>
```

Surface a terminal event as printed; it needs no feedback assessment. The
process exits after either event, which completes the harness monitor and
removes it from the active monitor count. For an open review, stop it manually
with pi's `monitor disarm <id>`, Claude Code's Monitor controls, or by killing
the process. There is no stop subcommand and no state on disk, so nothing needs
cleaning up and a new watcher re-baselines against whatever is already on the
review.
