---
type: Playbook
title: Showing authored prose for review before posting
description: Read before posting or editing prose under my name in Jira, merge requests, wikis, email, or tasks: how to show an edit as a diff, reference boilerplate instead of reproducing it, and present a batch whole
---
## Showing prose for review

The always-loaded rule says: show the full text and wait for an explicit yes.
This is how to show it.

- **Edit to existing text: show a diff.** Put a unified diff of the current text
  against the proposed text in a `diff` code block, with enough surrounding lines
  to place it. When most of the text changes, show the full new text as well. New
  text with nothing before it is shown in full, not as a diff.
- **Controlled boilerplate: reference it.** When most of the proposed text comes
  unchanged from a controlled or authoritative source (an MR template, a Jira
  issue template), identify that source and show how the proposal fills in or
  changes it: title and destination, human-authored prose, completed
  placeholders, role and quick-action assignments, checked or removed items, and
  other deviations. Give the complete rendered text when asked. Approval is still
  required before posting.
- **Batch: show it whole.** When one action writes prose to several places,
  present all of it in one pass, so earlier approvals are not already live while
  the rest is still under review.
- **Post what was approved,** not a re-worded version of it.

Merge request descriptions and review replies also follow
[change-requests.md](change-requests.md).
