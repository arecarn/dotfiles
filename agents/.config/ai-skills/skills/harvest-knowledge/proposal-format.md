# Proposal file format

One proposal file, `~/.local/state/knowledge-harvest/proposals/<date>.md`
(`<date>-2.md` and up for later runs the same day), is written per `run` and
edited in place by `review`. It carries everything review needs, so review
never has to reread the digests.

## Layout

The file has five parts, in this order:

1. **Header**: the run date; a `Run dir:` line with the run directory's
   absolute path; the number of sessions digested (`sessions` from `extract`);
   the number of sessions deferred to the next run (overflow plus failed
   batches); a `Deferred batches:` line listing the batch numbers whose reader
   failed, or `none`; and the ID-prefix mapping (see IDs). The next run's step 1
   reads the `Run dir:` and `Deferred batches:` lines to finish a run that died
   before committing its ledger, so write them exactly so.
2. **Summary table**: one row per item, columns `ID`, `Status`, `Destination`,
   `Change`. Review regenerates it from the items whenever a status changes.
   (The table review shows the user adds a `Recommended` column; the file's
   table does not carry it.)
3. **Items**: one block per item, grouped by prefix, in ID order.
4. **May be stale**: the `harvest.py stale` output, pasted whole. It supplies
   its own `## May be stale` heading, after a `Workspace roots:` line, so add
   no heading of your own.
5. **`## Dropped`**: counts of what consolidation dropped, one line per reason,
   for example `already covered: 41`. Counts only; no item text.

## IDs

An ID is an area prefix plus a number, for example `TT12`. Number each prefix
from 1. IDs never change once written: review refers to them across rounds and
sessions, and a dropped item keeps its ID.

- A bundle's prefix comes from the ID-prefix mapping. Copy the mapping from
  the newest proposal in `proposals/` or `proposals/done/`, so prefixes stay
  stable across runs. Derive a prefix only for a bundle that is not in it: the
  initials of its hyphen-separated words (`team-tools` gives `TT`), or the
  first two letters of a single-word id, uppercased, adding letters until it
  is unique. Keep every prefix distinct from `G`, `SK`, `PR`, and `RG`, and
  write the full mapping into the header.
- `G` for the general work bundle (see `routing.md`). The mapping records which
  bundle `G` is, or `unresolved` when discovery could not tell; review asks the
  user once and records the answer.
- `SK` for skills and instruction files.
- `PR` for preferences and corrections.
- `RG` for repository-gotcha suggestions (see `routing.md`).

## Item block

```markdown
### TT12

- **Status:** pending
- **Destination:** team-tools / build/cache.md (grow existing entry)
- **Change:** Say that the cache key includes the toolchain image digest
- **Text:**

  > The build cache key includes the toolchain image digest, so a new
  > image invalidates every cached object; the key is built in
  > `scripts/cache_key.sh`.

- **Evidence:** claude:3f2a…, confirmed against `scripts/cache_key.sh` on the default branch
- **Confidence:** high
- **Flags:** contradicts team-tools/build/cache.md
```

The bundle and paths in that example are invented; a real item names real ones.

| Field | Content |
| --- | --- |
| `Status` | `pending`, `kept`, `changed`, or `dropped`. `run` writes `pending`; only review changes it. |
| `Destination` | Bundle id and entry path, or `NEW: <title>` under the bundle; the skill or instruction file for `SK` and `PR`; the repository for `RG`. Add `(grow existing entry)` or `(new entry)`. |
| `Change` | One line saying what changes. This is the summary table's text, so it must read alone. |
| `Text` | The words as they would be written, pointer-style per `routing.md`. For `RG`, the trap as the suggestion would state it. |
| `Evidence` | The session keys (`source:id`, as in the digest filename) and how the item was confirmed. |
| `Confidence` | `high` or `medium`. Items below medium are dropped in consolidation. |
| `Flags` | Zero or more of `contradicts <entry>`, `unchecked` (a lookup the verifier needed failed), `time-sensitive` (the fact will expire, e.g. tied to a release). `none` when empty. |

Review adds two fields as it goes:

- `Reason`, when it sets `dropped`: the one-line reason, also used in the line
  appended to `dropped.md`. When it sets `changed`, it replaces `Text` with the
  agreed wording instead.
- `Landed`, once a `kept` or `changed` item is committed: the repository and
  commit, for example `dotfiles_local abc1234`. A `kept` or `changed` item with
  no `Landed` was approved but never landed, and the next review drafts it again.

## `dropped.md`

`~/.local/state/knowledge-harvest/dropped.md` holds one line per item review
dropped. Review appends a line for each drop, and removes it only when the user
reverses that drop:

```markdown
- 2026-11-16 TT12 team-tools/build/cache.md: <Change> — <Reason>
```

The date is the proposal's run date. Consolidation matches new candidates
against these lines, so the `Change` text must name the fact, not just the file.
