### Code Comments

Concision governs comments too, but under-commenting is the opposite failure,
not the safe one. A comment earns its keep by what the reader cannot get from
the code itself.

- **Aim above or below the code, never at it.** Above: the reasoning, or a
  one-line summary of a block. Below: the exact meaning, the boundary case. A
  comment pitched at the code's own level of detail is just the line again in
  prose.
- **Document the interface, not only the surprises.** A caller who cannot use a
  function without reading its body has no abstraction: state what it does, what
  it mutates, and what it requires of the caller. Brevity governs inline
  comments; an interface comment is finished when a caller needs nothing else.
- **Keep the caveat that prevents a wrong edit later:** the ordering that must
  hold, the invariant a type does not state, the second place that must change
  too. If you would have to explain it in review, comment it now, because that
  context belongs in the file rather than only in the conversation that produced
  it. Cut background that merely proves you did the research, and cite rather
  than reconstruct (a ticket, a requirement ID, a spec clause).
- **One comment, one job.** If a comment carries several unrelated facts, keep
  the one that changes what the reader does. Treat a long comment as suspect
  until you have checked it is not several facts competing: an algorithm's
  rationale may genuinely need a paragraph, and a line restating a line of code
  is too long at one line.
- **Keep comments true.** A comment that contradicts the code is worse than
  none, so update it in the same change as the code it describes. Do not copy a
  value that lives elsewhere; name where it lives and why it matters, so the
  comment survives the value changing.
