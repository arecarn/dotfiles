---
type: Reference
title: Paseo workspace and agent orchestration
description: Prefers Paseo for worktrees/agent orchestration; CLI syntax for running agents into worktrees, the --provider requirement, the branch-name-collision gotcha, and that its GitHub/GitLab integration needs gh or glab installed and authenticated since Paseo has no auth of its own
---
## Preference

Paseo (`@getpaseo`, getpaseo.com) is the preferred tool for worktree and agent
orchestration.

## Load the live command contract

Paseo has no `--skill` self-doc flag. `paseo --help` and `paseo <command>
--help` are authoritative for current syntax.

## Running an agent requires an explicit provider

`paseo run <prompt>` fails with "Provider is required" unless `--provider
<name>` is passed (e.g. `--provider claude`, `--provider claude/<model>`).
There is no default. Use `paseo provider ls` to see what's enabled in the
current environment.

## Creating a worktree session

`paseo run <prompt> --new-workspace worktree --worktree-mode <mode> ...`,
where `<mode>` is one of:

- `branch-off` — needs `--new-branch <name>`, optional `--base <ref>`
- `checkout-branch` — needs `--branch <name>`
- `checkout-pr` — needs `--pr-number <n>` and `--forge <forge>`

Add `--title <label>` for a readable name in `paseo ls`, and `-d`/
`--background` to not block the calling session.

### Gotcha: a stale worktree holding the branch forces a renamed copy

`checkout-branch` only reuses the exact branch name when that branch isn't
checked out anywhere else (it runs `git worktree list --porcelain` to check).
If it genuinely is checked out elsewhere — commonly a throwaway agent
worktree, e.g. under `.claude/worktrees/`, that built a PR and was never
cleaned up — Paseo can't check out the same branch twice (git wouldn't allow
it either), so it falls back to a new local branch named `<name>-1`,
leaving the local and remote names mismatched. This isn't a default to turn
off: the alternative would just be a hard git error instead of a rename.

The real fix is hygiene — remove or finish the worktree that's holding the
branch *before* starting a new session on it, so there's no collision and
Paseo uses the exact name. If a `-1` worktree already got created:
confirm the stale worktree is clean and pushed (`git status --short`),
remove it (`git worktree remove <path>`), then in the new worktree:

```
git branch -D <name>      # delete the now-freed, unused branch name
git branch -m <name>-1 <name>
git branch --set-upstream-to=origin/<name> <name>
```

## Inspecting and controlling agents

`paseo ls`, `paseo attach <id>` (stream live output), `paseo logs <id>`,
`paseo inspect <id>`, `paseo wait <id>`, `paseo send <id> <prompt>` (message a
running or idle agent), `paseo stop|archive|delete <id>`.

## Session paths

Worktree sessions land under `~/.paseo/worktrees/<workspace-slug>/<branch-or-slug>/`
by default. The daemon home defaults to `~/.paseo`, overridable with `--home`.

## Forge integration has no auth of its own

Paseo's GitHub/GitLab/Gitea integration (PR and MR status, checks, search,
merge) works by shelling out to the forge's own CLI — `gh` for GitHub, `glab`
for GitLab, `tea` for Gitea-family hosts — rather than holding any token or
OAuth credential itself. It detects which forge a repo's `origin` remote
belongs to by hostname (cloud hosts match directly; self-hosted hosts are
probed via `<cli> auth status --hostname <host>`), then drives that CLI.

**Setup requirement:** the relevant CLI must be installed and already
authenticated (`gh auth login` / `glab auth login`) on the machine before
Paseo's PR/MR features work for a given host. There is no separate Paseo login
step.
