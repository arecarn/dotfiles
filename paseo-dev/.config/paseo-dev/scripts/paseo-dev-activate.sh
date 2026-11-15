#!/usr/bin/env bash
# Activate the dev shell for the Paseo checkout or worktree in the current
# directory. Writes an untracked .envrc, excludes it through the repo's shared
# exclude file (linked worktrees share it), then asks direnv to allow it.
# Safe to repeat. Paseo's own files are never modified.

root=$(git rev-parse --show-toplevel)
exclude="$(git rev-parse --path-format=absolute --git-common-dir)/info/exclude"

# Nix refuses a flake path that is a symlink, and stow links the whole directory,
# so point at the resolved location.
flake=$(readlink -f "$HOME/.config/paseo-dev")
# PASEO_HOME from the host shell would point the dev stack at the real daemon's
# state; unsetting it makes the dev stack use the checkout-local .dev/paseo-home.
printf 'unset PASEO_HOME\nuse flake "path:%s"\n' "$flake" >"$root/.envrc"

mkdir -p "$(dirname "$exclude")"
touch "$exclude"
for entry in .envrc .direnv/; do
  grep -qxF "$entry" "$exclude" || echo "$entry" >>"$exclude"
done

direnv allow "$root"
