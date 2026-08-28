---
name: watch-review
description: Watch a GitLab merge request or GitHub pull request for feedback that is relevant to you, in the background, without spending model tokens on polling.
disable-model-invocation: true
---

# Watch Review

`watch_review.py` polls a review and prints one compact batch per poll of new
human feedback relevant to the authenticated user. **The polling is plain
Python: it costs no model tokens and prints nothing while nothing changes.**

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
python3 ~/.config/ai-skills/skills/watch-review/watch_review.py <review-url> [--interval 120] [--as-reviewer]
```

| Harness | Binding |
|---|---|
| pi | The `monitor` tool, armed with no `maxEvents` and `wake: true`. Unlimited because feedback arrives more than once; `wake: true` starts a turn as soon as a feedback batch arrives so it can be surfaced immediately. |
| Claude Code | Its `Monitor` background capability on the same command. |
| anything else | Whatever runs a command detached and reports its output later. |

Authentication comes from `glab` and `gh`, so neither a token nor a host needs
passing. Self-hosted GitLab and GitHub Enterprise work from the URL's hostname.

## Report batches verbatim

**Surface a batch exactly as printed and stop there.** No summarizing, no
ranking, no drafting a reply: the author and link are what make it actionable,
and rewording loses both. Say a batch arrived, show it, and wait. The watcher
only reads; it never replies, resolves, approves, or merges.

Stop it the ordinary way: pi's `monitor disarm <id>`, Claude Code's Monitor
controls, or killing the process. There is no stop subcommand and no state on
disk, so nothing needs cleaning up and a new watcher re-baselines against
whatever is already on the review.
