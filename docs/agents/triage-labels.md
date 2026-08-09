# Triage Labels

The skills speak in terms of five canonical triage roles. This file maps those roles to the actual label strings used in this repo's issue tracker.

| Label in mattpocock/skills | Label in our tracker | Meaning                                  |
| -------------------------- | -------------------- | ---------------------------------------- |
| `needs-triage`             | `needs-triage`       | Maintainer needs to evaluate this issue  |
| `needs-info`               | `needs-info`         | Waiting on reporter for more information |
| `ready-for-agent`          | `ready-for-agent`    | Fully specified, ready for an AFK agent  |
| `ready-for-human`          | `ready-for-human`    | Requires human implementation            |
| `wontfix`                  | `wontfix`            | Will not be actioned                     |

When a skill mentions a role (e.g. "apply the AFK-ready triage label"), use the corresponding label string from this table.

Edit the right-hand column to match whatever vocabulary you actually use.

## Local addition

| Label     | Meaning                                            |
| --------- | -------------------------------------------------- |
| `blocked` | Cannot proceed until an upstream dependency lands   |

`blocked` is a state label with no counterpart in the skills, so it takes the
place of a canonical state rather than sitting alongside one — a blocked issue
carries `blocked`, not `ready-for-human`.

**Applying `blocked` requires saying what it is blocked on.** The first line of
the issue body must be:

    Blocked by: <link or issue reference>, <one line on what has to happen>

Without it the label is unactionable — nobody can tell whether the blocker has
cleared, so the issue silently rots. If you cannot name the blocker, the issue
is not blocked; it is unclear, which is `needs-info`.

It exists because "ready" was a lie for issues waiting on an upstream fix: the
work is fully specified and nobody can start it. Move it to a canonical state
once the blocker lands.
