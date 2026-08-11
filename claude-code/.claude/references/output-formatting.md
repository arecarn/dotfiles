### Output Formatting

Rules for how responses are written, so they render correctly in the terminal.

- **Escape markdown metacharacters inside table cells.** A literal `|` ends the cell
  early and shifts every column after it; `*` and `_` are read as emphasis markers and
  mangle the row. Backticks do not reliably protect them — a cron expression like
  `0 */12 * * *` in a cell is enough to break the table. Escape as `\|` / `\*`, or move
  the value to a bullet beneath the table. A single bad cell is not a reason to stop
  using tables.
