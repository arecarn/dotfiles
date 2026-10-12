---
type: Playbook
title: Change request descriptions and review replies
description: Read when writing or editing a merge request or pull request description, or replying that review feedback was addressed: the final-diff rule, the Verification section, preserving templates, and naming the commit SHA
---
A **change request** is a merge request on GitLab or a pull request on GitHub.
Use the term the host uses in anything you write.

Posting is covered by the always-loaded rule on reviewing authored prose: show
the full text and wait for a yes first.

## Description

The description documents the **final diff against the base branch**. A reviewer
has the diff open, so the description orients and does not re-explain lines.

- **Shape.** One-line lead, then a few bullets grouped by the natural axis (for
  example per component). Add one tight clause of rationale only where the why is
  not obvious from the diff.
- **Cut.** Prose that a bullet repeats, line-by-line reasoning, addresses, and
  background the reviewer already knows. A bullet past a sentence or two is
  detail for a commit message or code comment. When in doubt, cut.
- **End state only.** Say what the code is now. If a reviewer diffs base..HEAD,
  every line must match what they see. Show a before and after only when it is
  the final fact (a renamed field's old and new value).
- **Leave the review out.** Earlier commits, what a reviewer asked for, tickets
  opened or closed during the change, and assertions tried and removed belong in
  commit messages and threads.
- **Verification section only when it adds something the pipeline does not:**
  tests added by this change, or manual checks done because automated testing was
  not possible (say what was done and why). CI status and test counts are already
  visible.
- **Editing an existing description:** keep any required template (checklists,
  roles, inputs) below the changes block and rewrite only the human-authored
  summary.

## Replying that review feedback is addressed

Name the commit SHA that contains the change. Use the shortest unambiguous SHA
Git shows, written as bare text so the host renders it as a commit link, for
example: “Updated in abc1234: replaced ‘fault signal’ with ‘status signal’.”
Include the SHA in every applicable thread reply, even when several replies point
to the same commit.
