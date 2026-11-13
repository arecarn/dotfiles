---
name: harvest-knowledge
description: Harvest durable facts, traps, and corrections from past agent sessions into knowledge bundles, skills, and instruction files, then review the proposals with the user. Use for the weekly scheduled run (a prompt starting `[harvest-knowledge] run`), when the user says "harvest knowledge", or when they say "review the harvest" or send `[harvest-knowledge] review`.
argument-hint: "run | review"
---

# Harvest knowledge

Past sessions hold facts that cost real work to find. This skill moves them
into the knowledge bundles in two halves, split where a human first becomes
necessary:

- **`run`** reads the sessions added since the last run and leaves a verified
  **proposal**. It is unattended and read-only outside its state directory.
- **`review`** walks the user through pending proposals in rounds, each built
  around an ID-numbered summary table, and lands only what they approve.

Pick the mode from the argument or the prompt. With neither, ask.

## Paths

```bash
SKILL=~/.config/ai-skills/skills/harvest-knowledge
STATE=~/.local/state/knowledge-harvest
```

Shell state may not persist between commands, so set both in every command
that uses them, or write the paths out.

- `$STATE/ledger.json`: per-session harvest offsets. Only `harvest.py commit`
  writes it.
- `$STATE/runs/<date>/`: one run's digests, batches, pending ledger, and,
  once `commit` has applied that ledger, a `committed` marker.
- `$STATE/proposals/<date>.md`: one proposal per run, in the form
  [`proposal-format.md`](proposal-format.md) defines. A second run on the same
  day writes `<date>-2.md`, then `-3`, and so on. Fully decided proposals move
  to `$STATE/proposals/done/`.
- `$STATE/dropped.md`: every item review dropped, with its reason.
- `$STATE/worktrees/<proposal stem>/`: review's staging worktrees for one
  proposal, keyed on its file stem (`2026-11-16-2` for `2026-11-16-2.md`), so
  two proposals from the same day never share one.

**Bundles** are discovered, never named. List them, with the private flag, by
calling the script's discovery function:

```bash
python3 - <<EOF
import sys; from pathlib import Path
sys.path.insert(0, "$SKILL"); import harvest
home = Path.home()
for b in harvest.discover_bundles(home / ".config/ai-knowledge", home / "dotfiles_local"):
    print(b.id, b.root.resolve(), "private" if b.private else "public")
EOF
```

A bundle is **private** when its link resolves under `~/dotfiles_local`, and
**public** otherwise. Each bundle's catalog is `<root>/index.md`.

## `run` mode

The prompt must start with `[harvest-knowledge] run`; that tag is what keeps
this session out of the next harvest. Write nothing outside `$STATE`. Allowed
beyond that: `git fetch`, reading files, and read-only queries to Jira, DNG,
and Blueserve.

### 1. Finish an interrupted run, then extract and batch

First look for a run that wrote its proposal but died before committing its
ledger: a `$STATE/runs/<date>/` holding `pending-ledger.json` but no
`committed` file, whose path a proposal in `$STATE/proposals/` or
`$STATE/proposals/done/` names on its `Run dir:` header line, where that
proposal file is newer than the `pending-ledger.json` (a same-day rerun reuses
the run dir, so an older proposal can name a newer pending ledger it never
read; skip that pairing). For each match, commit it now, passing
`--defer-batch N` for every N on that proposal's `Deferred batches:` line,
before anything else:

```bash
python3 $SKILL/harvest.py commit --run-dir <that run dir> --defer-batch <N> ...
```

Without this, its sessions would be digested and proposed again. A run dir
with no `committed` file and no proposal naming it died before its proposal;
leave it, since the next `extract` reads those sessions again anyway.

Then:

```bash
python3 $SKILL/harvest.py extract
python3 $SKILL/harvest.py batch --run-dir <run_dir>
```

`extract` prints JSON `{"run_dir", "sessions", "bytes"}`: it wrote one digest
per session with new messages to `<run_dir>/digests/<source>__<id>.md` and the
proposed offsets to `<run_dir>/pending-ledger.json`. The run date is
`<run_dir>`'s last path component.

When `sessions` is 0, skip to step 7 and report nothing new; there is no
proposal to write.

`batch` prints JSON `{"batches", "overflow_keys"}`: it wrote
`<run_dir>/batch0.txt` … `batch<N-1>.txt` (one absolute digest path per line)
and `<run_dir>/overflow.txt`. The overflow sessions are deferred to the next
run: `commit` reads `overflow.txt` itself, so `overflow_keys` is only for the
counts in the proposal header and the notification. Batches are filled in
read-first order (sessions deferred by an earlier run first, then oldest
first), so the overflow is always the newest sessions.

### 2. Read the digests

When `batches` is 1 and `bytes` is at most 300000, read every digest in
`batch0.txt` yourself, applying the reader brief below.

Otherwise dispatch one reader subagent per `batch<N>.txt`, all in parallel, on
a model cheaper than yours (in Claude Code, the Agent tool's `model`, for
example `sonnet` under an `opus` leader). Give each this brief, filled in:

> Read every digest file listed in `<run_dir>/batch<N>.txt`. Each starts with a
> `# session <id> source=<source> cwd=<cwd>` line, then one `USER:` or
> `ASSISTANT:` line per message.
>
> Find knowledge worth keeping beyond the session: a durable fact about a
> system or toolchain, a trap that cost real debugging, a correction of
> something an agent believed, or a preference or rule the user stated. Skip
> one-off task state, guesses the session never confirmed, and anything the
> session itself later retracted.
>
> First read these bundle catalogs, and report only what they do not already
> cover: `<each bundle id and its index.md path>`. A claim that differs from
> what an existing entry says is not covered: report it, and name that entry
> in **Suggested entry**.
>
> Report each item as:
>
> - **Bundle:** the bundle id, or `skill`, `instructions`, or `preference`
> - **Suggested entry:** an existing entry's path, or `NEW: <title>`
> - **Fact:** 1–4 specific sentences
> - **Evidence:** the session key `<source>:<id>` (from the digest filename)
>   and how the session confirmed it (a command's output, the code, a doc)
> - **Confidence:** `high` or `medium`
>
> Write nothing to any file. Return only the items.

If a reader errors or returns nothing, dispatch it once more with the same
brief. If the retry fails too, note its batch number N: step 6 defers that
batch with `--defer-batch N`, so its sessions are read next run rather than
lost, and the proposal header lists it under `Deferred batches`.

Every reader's report back (or its batch noted as deferred), or every digest
read yourself, completes the step.

### 3. Consolidate

Do this on your own model. Read [`routing.md`](routing.md), `$STATE/dropped.md`
(it may not exist yet), every pending proposal in `$STATE/proposals/` (not
`done/`), and every bundle entry a candidate touches. Then, for every
candidate:

- merge duplicates, keeping all their evidence;
- drop it if an entry already covers it, if it is one-off task state or an
  unconfirmed guess, if it matches a `dropped.md` line without new evidence, if
  an item in a pending proposal already proposes it (whatever that item's
  status, since review has not finished with it), or if a read-only Jira query
  finds it already recorded in a problem report;
- route it with `routing.md`, which also sets its ID prefix;
- flag it `contradicts <entry>` when it differs from an existing entry, and
  `time-sensitive` when it will stop being true on a known event or date (a
  release, a migration, a deadline, a temporary workaround);
- for a preference or correction, note where it already lives, if anywhere.

Tally every drop by reason for the proposal's `## Dropped` section. Assign IDs
as [`proposal-format.md`](proposal-format.md) describes. Mark for verification
every item flagged `contradicts`, and every `medium` item. Medium items are
where wrong facts land, so verifying them is a deliberate cost, not an
oversight.

### 4. Verify

Dispatch one verifier subagent, on your model, with the items marked for
verification (do it yourself when the harness has no subagents). Its brief:
for each item, check the claim against its source (the code on the default
branch, the cited doc, or a read-only Jira, DNG, or Blueserve query), and check
what the claim **means**, not only that it matches: a claim can match the code
and still be wrong about what it implies. For a `contradicts` item, look for
the reading under which both the item and the existing entry hold. Return, per
ID, one of: `confirmed`, `corrected` with the corrected text, `refuted` with
the reason, or `unchecked` with the lookup that failed.

Apply the results: correct the text, drop refuted items (counted under
`## Dropped`), and add the `unchecked` flag where a lookup failed. A failed
lookup never stops the run.

### 5. Write the proposal

```bash
python3 $SKILL/harvest.py stale
```

`stale` finds local checkouts under its workspace roots: each
`--workspace-root <dir>` given (repeat the flag for several), else the
`HARVEST_WORKSPACE_ROOTS` environment variable (directories separated by `:`,
`;` on Windows), else `~/files/projects` and its immediate subdirectories. When
the report's `Workspace roots:` line misses where this machine keeps its
checkouts, run it again with `--workspace-root`. Pass `--no-fetch` only when
the network is down.

It fetches each local checkout it resolves and prints a markdown report:
a `Workspace roots:` line, its own `## May be stale` heading over the entries
with commits to their cited files since their `verified` date, and an
`Unresolved sources:` count. Then write `$STATE/proposals/<date>.md` exactly as
`proposal-format.md` lays it out, with every item `pending`. If that file
already exists from an earlier run today, write `<date>-2.md`, and so on.

The proposal file existing on disk completes this step. Only then go on.

### 6. Commit the ledger

```bash
python3 $SKILL/harvest.py commit --run-dir <run_dir> --defer-batch <N> ...
```

`commit` defers every session in `<run_dir>/overflow.txt` on its own; never
copy overflow keys onto the command line. Pass `--defer-batch N` once per
batch whose reader failed in step 2, or omit it when none did. (`--deferred
<source>:<id>` defers one more session by key; the run never needs it.) A key
that is not in the run's pending ledger makes `commit` exit non-zero and change
nothing: report the error rather than guessing a fix. On success it writes
`<run_dir>/committed`.

Commit runs after the proposal file exists, never before: a run that dies
earlier leaves the ledger untouched, so the next run retries the same sessions,
and one that dies between the two is finished by step 1 of the next run.

### 7. Notify

Send one push notification (`PushNotification` in Claude Code) with the counts,
for example: `harvest-knowledge: 14 items proposed from 23 sessions, 3 deferred,
2 may be stale. Review with [harvest-knowledge] review.` Where the harness has
no push notification, print that line as the run's final message.

## `review` mode

Review runs in a session whose first message starts with
`[harvest-knowledge] review`, so the next harvest skips it and does not
re-propose what was dropped here. If this session started any other way, say so
and ask the user to start a fresh one with that message.

### Load the proposals

Take the files in `$STATE/proposals/` (not `done/`) oldest first: by run date,
then by numeric suffix, with an unsuffixed file first (`2026-11-16.md`, then
`2026-11-16-2.md`). Plain filename order gets same-day files wrong. Work on one
proposal at a time, starting at its first `pending` item. Items `kept` or
`changed` with no `Landed` field were approved in an earlier session but never
landed: draft them again with this session's work.

If the header's mapping leaves `G` (the general work bundle) unresolved, ask
the user once which bundle it is, and record the answer in the mapping before
the first round.

Before proposing any item from a proposal whose run date is more than four
weeks old, re-check it against its source, because facts drift. Correct it in
the file, or recommend `drop` with the reason.

Read every bundle entry an item touches before the first round, so each
recommendation rests on the current text.

### Rounds

A **round** covers about ten items, grouped by destination (one bundle, or the
`SK`, `PR`, or `RG` set). The **ID summary table** is the center of every
round: open with it, and come back to it after every answer.

| ID | Destination | Change | Recommended |
| --- | --- | --- | --- |
| TT4 | team-tools / build/cache.md | Name the file that builds the cache key | keep |
| TT5 | team-tools / NEW: Runner tags | Which runner tag the release job needs | change: drop the tag value, point at the CI file |
| TT6–8 | team-tools / gotchas/flaky-mount.md | Three confirmations of one mount trap | keep TT6, drop TT7–8 as duplicates |

(The rows are invented examples.) One row per item, `Change` copied from the
item's `Change` field, and a range only for items so related one answer fits
them all. Flags such as `contradicts` or `unchecked` go in the `Change` cell.

Below the table, tell the user how to answer:

- `keep TT4`, `drop TT5: <reason>`, `change TT6: <what to change>`, or
  `show TT6`;
- ranges and lists work: `keep TT6–8`, `drop TT2, TT9`;
- `rest as recommended` accepts every remaining recommendation in the round.

Then ask the round's open decisions (items where the recommendation is not
obvious, `contradicts` items, and `RG` suggestions) through AskUserQuestion when
the harness has it, one question per decision, recommended answer first. An
item the user has not answered stays `pending`; never treat silence as `keep`.

`show <ID>` prints that item's full `Text` and, once drafted, its diff against
the current entry. Show a full diff or file only for an ID the user names. The
user can `show` any ID at any time, including during the final summary.

As each answer comes in:

- write the item's `Status` into the proposal file, and regenerate the file's
  summary table;
- for `changed`, write the agreed wording into `Text`;
- for `dropped`, add the `Reason` field and append the item's line to
  `$STATE/dropped.md` (format in `proposal-format.md`); remove that line again
  if the user reverses the drop;
- for `RG`, `kept` means the user will act on it in that repository. Draft
  nothing for it.

Then print the updated table for the round. A round is complete when no item in
it is `pending`.

### Draft in a staging worktree

For every repository an accepted change lands in, find its main checkout with
`git -C <path> rev-parse --show-toplevel`, where `<path>` is the bundle's
resolved root, or the skill or instruction file's resolved directory. The
branch that checkout has out is the **target branch**. Create a staging
worktree outside the repository, at
`$STATE/worktrees/<proposal stem>/<repository dir name>`, on a new temporary
branch from the target branch. Draft every `kept` and `changed` item there.
Grow existing entries in place, and change an entry's `description` and its
index line together. When the repository generates its
instruction files from fragments, edit the fragment and regenerate. A memory
file outside any repository has no worktree: hold its change until the final
approval and write it then.

On resume, `git -C <main checkout> worktree list` shows a worktree left by an
interrupted review. Reuse it when its path is under this proposal's stem and
its branch holds only this proposal's drafts; otherwise remove it (`git
worktree remove`, then delete its branch) and draft afresh.

After every round, in each staging worktree with changes, run:

- the structure check on each touched bundle, `agent-knowledge check --path
  <bundle dir>`. When `agent-knowledge` is not on `PATH`, try
  `~/bin/agent-knowledge`, and failing that `uv run python -m
  manage.knowledge.cli check --path <bundle dir>` run from `~/dotfiles`, with
  `<bundle dir>` the absolute path of the bundle inside the staging worktree. It
  prints JSON and exits non-zero when `problems` is not empty;
- that repository's own lint and test targets (its `Makefile`, `tasks.py`, or
  instructions name them).

Fix what they report before the next round. When a fix changes the wording of
an item the user already answered, re-show that item's `Text` and diff and get
its answer again before the final summary.

### Land

When every item in the proposal is decided, show the proposal's
`## May be stale` list for information (re-verifying those entries is a
separate task the user may pick up). Then present one **final ID summary**:
the same table, listing every `kept` and `changed` item that will land, grouped
by repository, plus the `RG` suggestions the user kept to act on. Approving an
ID here approves that item's current `Text` and its drafted diff, both of which
`show <ID>` displays; say so above the table. Write nothing to a target branch
before the user approves this table.

On approval, for each repository:

1. Commit on the temporary branch, with the message
   `knowledge: <summary of what landed> (<landed IDs>)`, for example
   `knowledge: build cache key and mount trap (TT4, TT6)`.
2. If the target branch moved since the worktree was made, rebase onto it and
   re-run the checks.
3. Fast-forward the target branch in the main checkout to the temporary branch
   (`git merge --ff-only`). If the main checkout is not on the target branch, or
   has uncommitted changes to the touched files, stop and ask.
4. Run the repository's own stow task from its task runner (its `Makefile` or
   `tasks.py`), in the main checkout, so the change reaches the stowed paths.
   For `~/dotfiles` that is `uv run inv stow`.
5. Remove the staging worktree and delete the temporary branch.

Never push. Write any held memory-file change, then add a `Landed` field to
each landed item (format in `proposal-format.md`). When nothing in the proposal
was approved to land, there is nothing to commit, and this step is only the
move. Move the proposal to `$STATE/proposals/done/`, then go on to the next
pending proposal, or stop if the user wants to.

## Guardrails

- Write to a bundle, skill, or instruction file only after the user approved
  that exact change: its ID in the final ID summary, which covers the item's
  current `Text` and drafted diff.
- Put internal facts only in private bundles. A public bundle, skill, or
  instruction file gets the generic form, or nothing; check every public
  destination's text for names of work programs, hosts, systems, and
  repositories before the final summary.
- Read Jira, DNG, and Blueserve only. Write nothing to Jira, GitLab, or any
  project repository (a code repository, as opposed to the dotfiles
  repositories that hold the bundles, skills, and instruction files): an `RG`
  item is a suggestion the user acts on.
