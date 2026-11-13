# Routing harvested items

The consolidator's reference. Use it in `run` mode to decide, for each
candidate item, whether it lands at all and where. Apply every rule to every
item. An item routed by none of them is dropped as "no destination".

## Destinations

| Kind of item | Destination | ID prefix |
| --- | --- | --- |
| A durable fact about a program, system, or toolchain | an entry in the bundle that covers it | the bundle's prefix |
| A trap that belongs to one program | that program bundle's gotchas | the bundle's prefix |
| A trap in a toolchain shared across programs | the general work bundle's gotchas | `G` |
| A trap tied to one repository that has its own `docs/gotchas/` | a suggestion for that repository, not drafted | `RG` |
| A rule, workflow, or skill gap | a proposed edit to a skill or instruction file | `SK` |
| A preference or correction the user stated | a proposed edit to an instruction file, skill, or memory | `PR` |

Bundles come from discovery (see `SKILL.md`). A bundle is private when its
link resolves under `~/dotfiles_local`. The general work bundle is the private
bundle whose index says it covers work shared across programs; it is the only
one whose prefix is fixed, `G`. When no index claims that, or more than one
does, still route such items to `G`, record `G` as `unresolved` (or the
candidates) in the proposal header's mapping, and leave the choice to review,
which asks the user once.

## Rules

- **Reference over copy.** For any value that can go stale (a version, pin,
  count, timing, default, address, or path), name the file, constant, query,
  doc, or owning repository it lives in, and state only the durable behaviour
  or relationship. Let the repository that owns a pin track it.
- **Internal facts go only in private bundles.** A fact that names a work
  program, host, internal system, ticket project, or repository is internal.
  A public bundle, skill, or instruction file gets only the generic form, or
  nothing.
- **Rules and preferences are never bundle entries.** A bundle holds facts and
  procedures. "Always do X" and "the user prefers Y" are `SK` or `PR` items
  aimed at an instruction file, a skill, or memory.
- **A defect already recorded in a problem report is dropped.** The tracker
  holds it. Check with a read-only query before dropping on this ground.
- **A repository's own trap stays a suggestion.** When the trap belongs to one
  repository with its own `docs/gotchas/`, list it as an `RG` item naming the
  repository. Review shows it to the user, who acts on it separately; nobody
  drafts it here.
- **Grow before adding.** Prefer extending an existing entry over a new one.
  When a change alters what an entry covers, change its `description` and its
  index line together.
- **Leave what the code or an authoritative doc already says.** The code speaks
  for itself; an entry earns its place with what a reader cannot get by looking.
- **A gotcha needs all three:** it cost real debugging, it survives the fix,
  and nobody chose it. It ends with a `**Confirmed:**` line saying how it was
  reproduced. Missing any of the three, it is a fact entry, an ADR, or nothing.
- **Two sources can each be right.** When a session's claim differs from an
  existing entry or doc, look for the reading under which both hold (different
  roles, versions, layers, or meanings of one word) before calling either
  wrong. Flag the item `contradicts <entry>` and state both readings, so the
  verifier and the user decide; never rewrite the entry to match the session
  on the strength of the difference alone.
