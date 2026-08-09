---
description: Re-verify entries in docs/gotchas/ and delete the ones that stopped reproducing, so a stale trap never costs a read. Use when upgrading a tool or dependency an entry names, when an entry failed to help mid-debug, when a recorded symptom recurs, or when the user says "review gotchas" or "audit gotchas".
argument-hint: "[tool, entry, or area — omit to review everything in scope]"
---

# Review gotchas

An entry that no longer reproduces is worse than no entry: it costs a read and
teaches something false. Reviewing is how the directory stays worth reading, and
**deletion is the goal, not the failure case** — a trap engineered out of
existence beats the best entry describing it.

## 1. Select what to review

Reviews run on a trigger, not a calendar. Take the entries the trigger touches:

- **A tool or dependency moved** — every entry naming it. The upgrade you just
  pulled in may be the fix for the trap.
- **A symptom recurred** — the entry for it. Cheapest possible review, and the
  only one guaranteed to happen.
- **An entry did not help mid-debug** — that entry. Wrong, stale, or unfindable
  is a finding; fix it while you still know what you needed it to say.
- **No trigger given** — every entry whose `**Confirmed:**` line is oldest or
  says `unknown`.

Read each entry in full before judging it. `grep -ri "<term>" docs/gotchas/`
finds the ones naming a tool.

## 2. Try to reproduce each one

Run the trap against the code, config, and versions as they stand now — not
against your memory of it. An entry survives on evidence from today.

## 3. Take one of four outcomes

| Outcome | Action |
|---|---|
| Still reproduces | Update `**Confirmed:**` to today and to the version you just tested |
| Upstream fixed it | Delete the file — git keeps the history, and the entry named the version so a future reader can find it |
| A check now prevents it | Delete the file, and make the check's failure message say what it protects against |
| Cannot tell without re-running the incident | Leave it, and say so in the `**Confirmed:**` line — an honest "not re-verified since <date>" beats a date implying more than was done |

When an index `README.md` exists, its line goes in the same commit as the file.

## 4. Report what moved

Give the user one line per entry: reconfirmed, deleted, or left with a reason.
Name the deletions explicitly — they are the point of the exercise, and the user
may want to reverse one.

**Done when** every selected entry has been reproduced or explicitly ruled
untestable, and carries a `**Confirmed:**` line you can stand behind.
