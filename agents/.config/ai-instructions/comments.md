### Code Comments

Under-commenting is as much a failure as over-commenting. A comment earns its
keep by what the reader cannot get from the code itself.

- **Aim above or below the code, never at it.** Above: the reasoning, or a
  one-line summary of a block. Below: the exact meaning, the boundary case.
- **Document the interface.** A caller must not need the body: state what the
  function does, what it mutates, and what it requires of the caller.
- **Keep the caveat that prevents a wrong edit later:** the ordering that must
  hold, the invariant a type does not state, the second place that must change
  too. Cite a ticket or spec clause rather than reconstructing it.
- **Keep comments true.** Update them in the same change as the code. Name where
  a value lives instead of copying it.
