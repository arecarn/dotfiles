---
description: Record a trap in docs/gotchas/ so the same debugging is not paid for twice — decide whether it survives the fix, whether it is a gotcha or an ADR, and write it symptom-first with a Confirmed line. Use after root-causing surprising behaviour, when the user says "record this gotcha" or "add a gotcha", or when a fix lands whose cause would bite again.
argument-hint: "[the trap, if not already in context]"
---

# Record a gotcha

A **gotcha** is a trap: the system does something surprising, and nobody chose
it. Entries exist so a future reader — you, next month — skips the debugging
already done once.

Work the steps in order. Two of them end in writing nothing, and that is a
successful run.

## 1. Check whether the trap survived the fix

**Reproduce the trap against the code as it stands now.** The fix you just made
often removes the surprise entirely, and an entry describing a trap that no
longer exists costs a read and teaches something false.

Write nothing when:

- The fix **engineered it out** — the surprising behaviour is now impossible.
  Raising a version floor, deleting the code path, changing a default.
- A **check now prevents it** — a linter, a CI job, a `make` target. Put what
  the check protects against into its failure message instead, where someone
  meets it at the moment it matters.

Continue only when the trap still reproduces for the next person. Say which of
these you concluded and why, so the user can overrule it.

## 2. Route it: gotcha or ADR

- **Decided** — alternatives weighed, a call made, consequences accepted → write
  an ADR in `docs/adr/` instead, and stop here.
- **Discovered** — the system behaves this way and nobody chose it → a gotcha.
  Continue.

A trap whose fix required a decision produces both: the ADR records the call,
the gotcha records the behaviour that forced it.

## 3. Write the entry

One file per trap in `docs/gotchas/`, named for the trap and never numbered —
entries get deleted when they stop reproducing, and numbering would go gappy.

```markdown
# <the symptom, as a short label>

**<the trap stated in full, in one sentence>**

<what is actually going on, then how to get past it. Three lines for a simple
trap, a page for a multi-part incident — whatever it needs.>

**Confirmed:** <date> against <the version, image tag, or config file it
reproduced on>
```

Four rules carry the weight:

- **Lead with the symptom** — in the heading and in the first sentence. The
  symptom is what a reader greps for mid-debug; they do not yet know the cause,
  which is why they are reading.
- **Name the file for the trap**, matching the symptom
  (`windows-symlink-creation-needs-elevation.md`).
- **Keep the wrong turns.** Every other doc states current facts; entries record
  what was ruled out, because that is what stops the re-derivation.
- **End with `**Confirmed:**`** — the date it last reproduced and what against.
  Without it a live trap reads identically to one upstream fixed two years ago.
  State only what you actually verified: for a trap you inherited rather than
  reproduced, write `unknown, predates this convention`.

## 4. Create the convention if this is the first entry

When `docs/gotchas/` does not exist, create it with this entry, and add a
**Gotchas** section to `AGENTS.md` (or `CLAUDE.md`) covering: one trap per file
named for the trap, unnumbered because entries are deleted; gotcha versus ADR;
the `**Confirmed:**` line; and review on a trigger with deletion as the goal.
Point the repo's agent docs at the directory alongside `docs/adr/`.

Add an index `README.md` only once skimming `ls` has actually become hard —
around a dozen entries. Below that it is a second file to keep in sync.

## 5. Commit it with the fix

The entry belongs in the same commit as the fix that provoked it, so the trap
and its evidence arrive together.

**Done when** the trap reproduces or is ruled out on today's code, the entry is
written or consciously skipped with a reason, and every `**Confirmed:**` claim
is one you verified.
