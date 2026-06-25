### Merge Request / Pull Request Descriptions

**Clear, concise, plain wording, no jargon.** This is the overriding rule for
every MR/PR description. Spell things out; avoid coinages and shorthand
("de-A'd", "GS1-shaped"). Lead with the changes, grouped by the natural axis
(e.g. cases vs procedures, per component). Write for a reviewer who has the diff
open and wants the summary in plain language.

The description documents the **final diff against the base branch**, not a
changelog of the review.

- **Describe the end state, not the journey.** Say what the code/cases/procedures
  *are* now, not how they got there. Drop "rebuilt", "reworked after X failed",
  "no longer does Y", "review refinement", "previously", "switched from". If a
  reviewer diffs base..HEAD, every line of the description should match what they
  see; nothing should describe an intermediate state that no longer exists. State
  a concrete before/after only when it *is* the final fact (e.g. a renamed field's
  old and new value); otherwise just the new value.
- **No review-history narration.** Don't mention earlier commits, what a reviewer
  asked for, tickets opened/closed during the MR, or assertions that were tried
  and removed. Those live in commit messages and threads, not the description.
- **Don't recap CI in a Verification section.** "CI passing" and test counts
  (e.g. "12 tests pass") are visible on the MR and add nothing. Only include a
  Verification section when it conveys something the pipeline does not: tests
  *added* as part of this change, or manual verification performed *because*
  automated testing wasn't possible in the MR (say what was done and why it
  couldn't be automated). If neither applies, omit the section.
- When editing an existing MR description, **preserve any required template**
  (checklists, roles, inputs) below the changes block; only rewrite the
  human-authored summary.
