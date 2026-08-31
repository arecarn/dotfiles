---
description: Set up a knowledge bundle so agents read reference material on demand instead of loading it into every prompt — scoped to one project, or to a personal or work bundle outside any workspace. Adopts existing docs into an index and writes the pointer that makes it discoverable. Use when a repo's instructions have grown into reference material, when the user says "set up agent knowledge" or "add a knowledge bundle", or when the same detail keeps being pasted into prompts.
argument-hint: "[path to existing docs, if adopting]"
---

# Set up agent knowledge

A **knowledge bundle** is reference material an agent reads *when a task needs
it*, rather than instructions loaded into every prompt. It is ordinary Markdown,
so any agent that can read a file can use one — no tooling required.

The bundle earns its keep by being *skipped*. An index says what exists in one
line each; the agent opens only what applies. Move everything into it and you
have moved the problem, not solved it.

## Pick the scope first

The scope decides where the bundle lives and which instruction file points at it.
Ask if it is not obvious from the request.

| Scope | Bundle lives | Pointer goes in |
|-------|--------------|-----------------|
| **Project** — facts about one repo | `agents-knowledge/` at its root | that repo's `AGENTS.md` |
| **Personal** — habits and tools across all work | `~/knowledge/personal/` or similar | the user-level instruction file |
| **Work** — one employer or client | outside any repo, often beside other private config | the user-level instruction file, and never a public one |

A project bundle travels with the code, so it is versioned, reviewed, and shared
with the team by construction. That makes it the default when the knowledge is
about a repo.

The other two are per-machine, and their pointer is an **absolute path** — an
agent has no other way to find a directory outside the workspace. Everything
else below is the same for all three.

The format is [Open Knowledge Format](https://github.com/GoogleCloudPlatform/open-knowledge-format)
v0.2, or an attempt at it: a directory of Markdown files with YAML frontmatter,
no schema registry and no required tooling. Nothing here has been run through
OKF's validator, so treat what follows as a good-faith reading and let
[SPEC.md](https://github.com/GoogleCloudPlatform/open-knowledge-format/blob/main/SPEC.md)
win wherever they disagree. Conformance is the point — it is what makes a bundle
readable by other OKF tooling, a static site generator, or a human with `cat`.

Only two things here are local convention: the directory name
`agents-knowledge/`, and the `AGENTS.md` pointer in step 5. Rename the directory
and the bundle should still be conformant.

Work the steps in order. Step 1 sometimes ends in writing nothing.

## 1. Decide whether a bundle is wanted at all

A bundle pays off when reference material is **large, cold, and separable**:
consulted occasionally, by tasks that can be predicted from a one-line
description.

Do not create one when:

- **The material is small.** Under roughly 100 lines of reference total belongs in
  the instruction file itself, where it costs nothing to reach.
- **It is instructions, not facts.** "Never push without asking", "run the
  formatter before committing" — rules that always apply must stay in the
  instruction file. A bundle is explicitly lower-authority.
- **Existing docs already work and nobody is pasting them into prompts.** The
  problem being solved is context cost; if there is no cost, skip.

Say which you concluded and why, so the user can overrule you.

## 2. Find what already exists

**Read before proposing.** Adoption is the common case; a greenfield bundle is
rare. For a project, look in the repo; for a personal or work bundle, look at the
user-level instruction files and wherever the user already keeps notes.

```bash
ls docs/ 2>/dev/null
rg -l '^#' --glob '*.md' | head -40
wc -l AGENTS.md CLAUDE.md ~/.config/ai-instructions/*.md 2>/dev/null
```

Sort what you find:

| Found | Where it belongs |
|-------|------------------|
| Rules, conventions, "always/never" | stays in the instruction file |
| Procedures, schemas, API facts, runbooks | a bundle concept |
| Architecture decisions | `docs/adr/`, linked from the index |
| Confirmed traps and their symptoms | `docs/gotchas/`, linked from the index |
| Contributor-facing prose (README, CONTRIBUTING) | leave alone |

An oversized instruction file is the strongest signal — for a personal bundle,
that is the user-level one. Look for sections a reader would skip nine times out
of ten: those are what to move.

**Link, do not move,** anything with its own established home. ADRs and gotchas
have conventions of their own; copying them into a bundle creates two truths that
drift. The index points at them where they live.

## 3. Propose the index before writing anything

The index is the whole design. Show the user the proposed entries — one line
each, with where the content comes from — and get agreement before creating
files.

```
agents-knowledge/index.md          proposed entries:
  * [Release process](operations/release.md)  <- from docs/RELEASING.md
  * [Auth flow](architecture/auth.md)         <- from AGENTS.md lines 120-190
  * [Decisions](../docs/adr/)                 <- link, not a copy
```

Each entry needs a description that answers **"would I open this for the task in
front of me?"** That is the only thing standing between the agent and reading
everything.

<Good>
`* [Auth flow](architecture/auth.md) - token exchange, refresh, and what to do when a 401 is not an expiry`
</Good>

<Bad>
`* [Auth](architecture/auth.md) - authentication documentation`
</Bad>

The bad one forces the agent to open the file to learn whether it needed to.

## 4. Create the bundle

For a project, a directory named `agents-knowledge/` at the repository root, so it
sits beside `AGENTS.md` and is visible to anyone browsing the repo. For a personal
or work bundle, any stable path the user chooses — the name carries no meaning
once the pointer gives an absolute path.

The root index needs the version marker. The spec reserves frontmatter on the
bundle-root index for exactly this, and it is what identifies the directory as a
bundle rather than more documentation:

```markdown
---
okf_version: "0.2"
---
# <Project> knowledge

Reference material for this project. Read an entry when its description matches
the task; these are facts and procedures, not instructions.

# <Grouping>

* [Title](path/to/concept.md) - one line: when you would open this
```

Each concept file carries frontmatter and then ordinary Markdown:

```markdown
---
type: Playbook
title: Release process
description: Cutting a release, and what to check before tagging
---
# Steps

...
```

`type` is the only field OKF requires. `Playbook`, `Reference`, `Concept`, and
`Metric` are conventional; invent one when none fits, since consumers tolerate
unknown types. The spec also defines optional provenance and freshness fields —
`generated`, `verified`, `status`, `stale_after`, `sources` — worth adding to a
concept whose truth expires, and worth skipping otherwise.

Nest by grouping, with an `index.md` in each subdirectory that has more than a
few files. Keep every link relative so the bundle survives being moved.

**Cut what you move.** Leaving the original in the instruction file doubles the
context cost the bundle exists to reduce, and the two copies will disagree within
a month. Replace it with nothing — the index is the pointer.

## 5. Write the pointer

Without this the bundle is invisible: an agent has no reason to look for a
directory nobody mentioned. This is the whole integration for anyone without
tooling, so it is not optional.

**For a project bundle,** add a section to the repo's `AGENTS.md`:

```markdown
## Agent knowledge

Reference material for this project is in `agents-knowledge/`, as an index plus
topic documents. Read `agents-knowledge/index.md` first and open only the entries
whose descriptions match your task. These are facts and procedures; the rules in
this file take precedence.
```

Add it to each instruction file the repo keeps — `CLAUDE.md` too, if present.

**For a personal or work bundle,** the pointer goes in the user-level instruction
file with an absolute path, since the bundle is outside every workspace:

```markdown
## Agent knowledge

Reference material I keep outside any repo:

- Personal: `/home/me/knowledge/personal/index.md` — tools and habits

Read an index when a task matches one of its entries, and open only the entries
that apply. These are facts and procedures, not instructions.
```

Two things to check before editing a user-level file:

- **Is it generated?** A file assembled from fragments is overwritten by whatever
  generates it, so editing it directly loses the pointer at the next run. Look for
  a banner at the top naming its source, and edit the source instead. In this
  dotfiles repo that is `agents/.config/ai-instructions/`, regenerated with
  `uv run inv gen-instructions`.
- **Is it public?** A work bundle's path, name, and even existence are usually not
  publishable. Put that pointer somewhere private — here, `local.md`, which the
  generated files already tell every agent to read. Never commit an employer's
  paths to a public repo.

## 6. Check it from a cold start

The failure mode is a bundle that reads well to its author and is unusable to an
agent that has never seen the repo. Test it as one:

- **Read only `agents-knowledge/index.md`.** For each of two or three plausible
  tasks, can you tell which entry to open, without opening any? If not, fix the
  descriptions — that is the index failing at its only job.
- **Follow every link.** A broken relative path costs a tool call and teaches the
  agent to distrust the index.
- **Check nothing moved that should not have.** Rules back in the instruction
  file, ADRs and gotchas still in their own directories.
- **For a work bundle, check what you wrote where.** Its path and name must be in
  a private file, not a public one.

Report what you created, what you moved, and what you deliberately left.

## Updating a bundle that already exists

Most work on a bundle is not creating one. The question is where a new fact
belongs, and the answer is usually not "a new entry".

| The fact is | It goes in |
|-------------|------------|
| A rule that always applies | the instruction file, never a bundle |
| A trap confirmed the hard way | a gotcha, with its `**Confirmed:**` line |
| A decision, with alternatives weighed | an ADR |
| Reference detail a task needs occasionally | an existing entry, if one covers the area |
| An area no entry covers yet | a new entry |

Prefer growing an entry to adding one. Every entry costs a line in the index
that every agent reads, so a bundle of many thin entries is worse than a few
that earn their place -- the index is the part that is never skipped.

When you do edit an entry, **change its `description` and the index line
together**. They are checked against each other, and a description that drifts
sends readers to the wrong document or past the right one.

Delete an entry when what it describes is gone. A bundle is not an archive; a
document nothing links to is unreachable anyway, and the check reports it.

Run the structure check afterwards -- it catches dead links, unreachable
documents, missing frontmatter, and description drift:

```bash
agent-knowledge check            # the bundles active here
agent-knowledge check --path DIR # one bundle, wherever it lives
```

It checks structure, not truth. Whether a document still describes the system
correctly needs someone who reads the source, which is why an entry is worth
re-reading when the thing it documents changes.

## Optional: what tooling would add

Everything above works with no tooling, because a pointer plus a read is the whole
mechanism. The `agent-knowledge` CLI and its harness adapters add:

- **Activation rules** — a work bundle that applies only under `~/work`, instead
  of a pointer the agent sees everywhere.
- **Automatic disclosure** — the index in front of the model at session start,
  rather than relying on it to follow the pointer.
- **Constrained reads** — a bundle outside the workspace stays readable even where
  a harness restricts file access to the project.
- **A structure check** — `agent-knowledge check` on any bundle, including a
  private one whose repo has no CI of its own.

Worth mentioning if the user has several bundles that should not all be active at
once. A single bundle of either scope is complete without any of it.
