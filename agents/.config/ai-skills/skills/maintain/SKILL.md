---
name: maintain
description: Use when asked to update, upgrade, or refresh the agent tooling or dotfiles -- Claude Code, pi, their plugins, pi model catalogs, a dotfiles pull, or a restow -- or for a routine maintenance pass over this machine's AI setup.
---

# Maintain

One command does the routine pass; this skill is how to run it and what to do
with the result.

```bash
cd ~/dotfiles && uv run inv maintain            # everything
cd ~/dotfiles && uv run inv maintain --only pull,stow
cd ~/dotfiles && uv run inv maintain --skip cli
```

Run it from the **main checkout**, not a linked worktree. The `stow` group
refuses a worktree, because the home-directory symlinks would point into it
and dangle once it is removed.

## Groups, in run order

| Group | Does |
|---|---|
| `pull` | `git pull --ff-only` in `~/dotfiles` and `~/dotfiles_local`. Never stashes. A dirty tree is pulled when git allows it and skipped, with git's reason, when an incoming change overlaps a local edit or history diverged. |
| `cli` | Upgrades Claude Code (npm) and pi (pnpm) with user-level commands. Reads the package list from `ansible/group_vars/all.yml`, so it never prompts for sudo. |
| `plugins` | Claude plugin updates, pi package updates, `pi update --models`. |
| `stow` | `inv stow` and `inv stow-skills`. Skipped when `~/dotfiles` was not pulled. |
| `local` | Runs `~/dotfiles_local/scripts/maintain-local` if present (private checks such as the gateway model list). |

System packages are out of scope: they need sudo, so they stay with `inv provision`.

## After the run

1. **Revert the lock rewrite.** `uv run` rewrites `uv.lock` to an internal
   registry. Run `git checkout -- uv.lock` in `~/dotfiles`; never `git add -A` there.
2. **Report** the summary the task prints: each group's outcome, and the
   before/after versions of `claude` and `pi`. Name any repo `pull` skipped and
   git's reason.
3. **Read out anything `local` flagged.** A model-list difference is a decision
   for the user, not an edit to make unasked: say what the gateway serves that
   `models.json` lacks, and offer to add it.
4. **Offer to commit** uncommitted changes in `~/dotfiles_local`; push only if asked.
5. A running Claude session keeps its old version. Say a restart is needed to use the new one.

A `FAILED` group does not stop the others. Report it and its message; do not
retry blindly.
