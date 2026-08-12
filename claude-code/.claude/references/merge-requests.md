### Merge Request / Pull Request Descriptions

**Clear, concise, plain wording, no jargon.** This is the overriding rule for
every MR/PR description. Spell things out; avoid coinages and shorthand. Lead
with the changes, grouped by the natural axis (e.g. per component). Write for a
reviewer who has the diff open and wants the summary in plain language.

**Default to short.** A reviewer has the diff open; the description orients, it
does not re-explain every line. Aim for a one-line lead plus a few grouped
bullets. One tight clause of rationale per change only where the "why" is not
obvious from the diff. Do not restate a change in prose and again in a bullet,
do not narrate disassembly/addresses/line-by-line reasoning, and do not pad with
background the reviewer already knows. If a bullet runs past a sentence or two,
it is probably detail that belongs in a commit message or code comment, not the
MR description. When in doubt, cut.

The description documents the **final diff against the base branch**, not a
changelog of the review.

- **Describe the end state, not the journey.** Say what the code *is* now, not
  how it got there. Drop "rebuilt", "reworked after X failed", "no longer does
  Y", "review refinement", "previously", "switched from". If a reviewer diffs
  base..HEAD, every line of the description should match what they see; nothing
  should describe an intermediate state that no longer exists. State a concrete
  before/after only when it *is* the final fact (e.g. a renamed field's old and
  new value); otherwise just the new value.
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
