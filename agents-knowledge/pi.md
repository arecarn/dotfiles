---
type: Reference
title: Pi configuration
description: What lives in pi/.pi/agent/, how a pi package is declared, and the fold barrier a package with its own config must get or its files land in this public repo
---
# Layout

`pi/.pi/agent/` holds pi's generated `AGENTS.md` and `extensions/` (TypeScript,
linted and type-checked by `inv lint`). Plain `ls pi/` looks empty -- everything
is under the dot-prefixed `.pi`.

# Adding a package

Declare it with a `pi_package:` key in `agents/.config/ai-skills/plugins.yaml`
(stowed to `~/.config/ai-skills/plugins.yaml`), whose source spec takes
`npm:name`, `npm:name@version`, or `git:host/user/repo`. That is the only place
pi packages are listed; `manage/agents/plugins.py` picks up any entry with the
key, so no code changes.

Then `inv pi-setup` writes the packages into pi's own
`~/.pi/agent/settings.json` -- generated, never hand-edited, which is what keeps
the preferences pi writes there out of this repo -- and `inv pi-install-plugins`
runs the install.

A work-specific package goes in a `dotfiles_local` repo's `plugins_local.yaml`,
which replaces a base entry of the same name outright rather than merging keys.

# A package with its own config needs a fold barrier

A package that reads its own config file gets it here as
`pi/.pi/agent/extensions/<package>/config.json`, as `extensions/subagent/` does.

That same directory is where pi's installer git-clones the package and writes
back. dploy folds a directory this repo fully owns into a single symlink, so
without a barrier everything the installer writes lands inside the working tree
of a public repo. **Add `.pi/agent/extensions/<package>` to `_FOLD_BARRIERS` in
`manage/stow.py` in the same change as the config file.** Adding the config and
forgetting the barrier is the silent failure.

# What pi does not ship

No MCP or subagent support, by design; both come from third-party packages.
Skills arrive via the shared hub fan-out, not the package.
