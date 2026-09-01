### Code Comments

**Default to no comment.** Most code needs none: clear names and small
functions carry the meaning, and a comment that repeats them is noise a future
reader has to check against the code. Write one only when the reader cannot get
the fact from the code itself, and prefer fixing the name or the structure over
explaining it in prose.

- **Never narrate the code.** No comment that restates the line or block below
  it, labels an obvious step ("loop over the items", "handle the error", "set up
  the client"), announces a section of a short function, or explains what a
  well-named call already says. If a reviewer could delete the comment and lose
  nothing, do not write it.
- **Do not comment your own work.** Comments explaining what changed, why you
  chose this approach over another, or that something was added for a request
  belong in the commit message or the merge request, not the file.
- **Aim above or below the code, never at it.** Above: the reasoning. Below: the
  exact meaning, the boundary case. A comment pitched at the code's own level of
  detail is just the line again in prose.
- **Do document the interface.** A caller who cannot use a function without
  reading its body has no abstraction: state what it does, what it mutates, and
  what it requires of the caller. This is the one place length is earned, and it
  is finished when a caller needs nothing else. Skip it for a function whose
  signature already says everything.
- **Keep the caveat that prevents a wrong edit later:** the ordering that must
  hold, the invariant a type does not state, the second place that must change
  too. If you would have to explain it in review, comment it now. Cut background
  that merely proves you did the research, and cite rather than reconstruct (a
  ticket, a requirement ID, a spec clause).
- **One comment, one job.** If a comment carries several unrelated facts, keep
  the one that changes what the reader does. An algorithm's rationale may
  genuinely need a paragraph; a line restating a line of code is too long at one
  line.
- **Keep comments true.** A comment that contradicts the code is worse than
  none, so update it in the same change as the code it describes. Do not copy a
  value that lives elsewhere; name where it lives and why it matters, so the
  comment survives the value changing.
- **Match the file you are in.** Comment density is a property of the codebase,
  not of you. Where surrounding code is sparse, stay sparse.
