# Triage Labels

The skills speak in terms of five canonical triage roles. This file maps those roles to the actual label strings used in this repo's issue tracker.

| Label in mattpocock/skills | Label in our tracker | Meaning                                  |
| -------------------------- | -------------------- | ---------------------------------------- |
| `needs-triage`             | `needs-triage`       | Maintainer needs to evaluate this issue  |
| `needs-info`               | `needs-info`         | Blocked on information the owner has to go find |
| `ready-for-agent`          | `ready-for-agent`    | Fully specified, ready for an AFK agent  |
| `ready-for-human`          | `ready-for-human`    | Requires human implementation            |
| `wontfix`                  | `wontfix`            | Will not be actioned                     |

When a skill mentions a role (e.g. "apply the AFK-ready triage label"), use the corresponding label string from this table.

Edit the right-hand column to match whatever vocabulary you actually use.

## Labels carry state, bodies describe work

The label communicates the state of the ticket. The body describes the work or
the problem the ticket represents. Nothing in a body should name a label or
argue for the state it was given — not "labelled `ready-for-human` because…",
not "this is `needs-info` until…".

Such a sentence is wrong the moment the label changes, and nothing forces the
two back into agreement, so the body ends up asserting a state the tracker
disagrees with. The reasoning it tries to preserve is better expressed as the
fact underneath it: not "labelled `ready-for-human` because it needs a real
Wayland session", just "verifying this needs a real Wayland session". That
sentence stays true whatever the label says, and a reader can see the state
without being told it twice.

The `blocked` state's required `Blocked by:` first line is not an exception. It
names another ticket or an upstream issue, which is a fact about the work; it
does not name the label or justify it.

## Local additions

### Extra state

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

### Closure reasons

| Label       | Meaning                                        |
| ----------- | ---------------------------------------------- |
| `duplicate` | Already tracked by another issue               |
| `invalid`   | Not a real defect, or not actionable as filed  |

These sit *alongside* `wontfix`, never instead of it — the state stays readable
on its own, and the reason label records why without having to open the issue.
They do not replace the closing comment: say which issue it duplicates, or why
it is invalid. A label is a filter, not an explanation.

## This tracker has one participant

Every issue here is filed by the repo owner. The repo is public, but no one else
has ever opened an issue or a pull request.

`needs-info` still applies — plenty of issues wait on something being reproduced,
checked upstream, or seen to recur. What changes is who owes the answer: the
owner does, so nothing arrives to clear it. The skills re-surface a `needs-info`
issue on reporter activity, and that event will never fire here, so treat the
`needs-info` bucket as a list to revisit deliberately rather than one that
refills itself.

There is no `question` label, because a question needs someone else to be asking
it.

Revisit this section if the repo ever attracts outside issues.

## Not triage labels

`dependencies`, `python`, and `python:uv` are created and applied by Dependabot
on its own pull requests. Ignore them when triaging, and do not apply them by
hand — deleting them achieves nothing, as the next Dependabot PR recreates them.
