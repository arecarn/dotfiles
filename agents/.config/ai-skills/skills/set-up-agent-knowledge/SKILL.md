---
description: Give a project an agents-knowledge/ bundle so agents read reference material on demand instead of loading it into every prompt — adopt existing docs into an index, or scaffold a new one, and point AGENTS.md at it. Use when a repo's instructions have grown into reference material, when the user says "set up agent knowledge" or "add a knowledge bundle", or when detail keeps being pasted into prompts.
argument-hint: "[path to existing docs, if adopting]"
---

# Set up agent knowledge

An **agents-knowledge bundle** is reference material an agent reads *when a task
needs it*, rather than instructions loaded into every prompt. It is ordinary
Markdown in the repo, so any agent that can read a file can use it — no tooling
required.

The bundle earns its keep by being *skipped*. An index says what exists in one
line each; the agent opens only what applies. Move everything into it and you
have moved the problem, not solved it.

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

## 1. Decide whether this project wants one

A bundle pays off when reference material is **large, cold, and separable**:
consulted occasionally, by tasks that can be predicted from a one-line
description.

Do not create one when:

- **The material is small.** Under roughly 100 lines of reference total belongs
  in `AGENTS.md`, where it costs nothing to reach.
- **It is instructions, not facts.** "Never push without asking", "run the
  formatter before committing" — rules that always apply must stay in
  `AGENTS.md`. A bundle is explicitly lower-authority.
- **Existing docs already work and nobody is pasting them into prompts.** The
  problem being solved is context cost; if there is no cost, skip.

Say which you concluded and why, so the user can overrule you.

## 2. Find what already exists

**Read before proposing.** Adoption is the common case; a greenfield bundle is
rare.

```bash
ls docs/ 2>/dev/null
rg -l '^#' --glob '*.md' | head -40
wc -l AGENTS.md CLAUDE.md 2>/dev/null
```

Sort what you find:

| Found | Where it belongs |
|-------|------------------|
| Rules, conventions, "always/never" | stays in `AGENTS.md` |
| Procedures, schemas, API facts, runbooks | a bundle concept |
| Architecture decisions | `docs/adr/`, linked from the index |
| Confirmed traps and their symptoms | `docs/gotchas/`, linked from the index |
| Contributor-facing prose (README, CONTRIBUTING) | leave alone |

An oversized `AGENTS.md` is the strongest signal. Look for sections a reader
would skip nine times out of ten: those are what to move.

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

Directory named `agents-knowledge/` at the repository root, so it sits beside
`AGENTS.md` and is visible to humans browsing the repo.

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

**Cut what you move.** Leaving the original in `AGENTS.md` doubles the context
cost the bundle exists to reduce, and the two copies will disagree within a
month. Replace it with nothing — the index is the pointer.

## 5. Point AGENTS.md at the bundle

Without this the bundle is invisible: an agent has no reason to look for a
directory nobody mentioned. Add a short section — this is the whole integration
for anyone without tooling:

```markdown
## Agent knowledge

Reference material for this project is in `agents-knowledge/`, as an index plus
topic documents. Read `agents-knowledge/index.md` first and open only the entries
whose descriptions match your task. These are facts and procedures; the rules in
this file take precedence.
```

Adjust the filename if the project uses `CLAUDE.md` or another instruction file,
and add it to each one the project keeps.

## 6. Check it from a cold start

The failure mode is a bundle that reads well to its author and is unusable to an
agent that has never seen the repo. Test it as one:

- **Read only `agents-knowledge/index.md`.** For each of two or three plausible
  tasks, can you tell which entry to open, without opening any? If not, fix the
  descriptions — that is the index failing at its only job.
- **Follow every link.** A broken relative path costs a tool call and teaches the
  agent to distrust the index.
- **Check nothing moved that should not have.** Rules back in `AGENTS.md`, ADRs
  and gotchas still in their own directories.

Report what you created, what you moved, and what you deliberately left.

## Optional: activation beyond one project

Everything above is per-repository and needs no tooling. Two things do:

- **Personal or work bundles outside the repo** — knowledge that applies across
  projects, which an agent cannot reach because it is outside the workspace.
- **Automatic disclosure** — putting the index in front of the model at session
  start rather than relying on it to look.

Both come from the `agent-knowledge` CLI and its harness adapters. Mention them
only if the user asks for cross-project knowledge; a project bundle is complete
without them.
