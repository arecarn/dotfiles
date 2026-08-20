# Reconcile pi packages via `pi update --extensions` instead of `pi install`

Pi packages are declared by a `pi_package:` key in
`agents/.config/ai-skills/plugins.yaml`. `uv run inv pi-setup` writes them into
the `packages` array of pi's own `~/.pi/agent/settings.json`, and
`uv run inv pi-install-plugins` reconciles installed packages against that array
by running `pi update --extensions`, rather than running `pi install <source>`
once per declared package.

## Why

`pi install <source>` writes to `settings.json` whenever the source is not
already in the `packages` array. When this repo committed that file and stowed
it as a symlink, every such write landed on a committed file. The file is no
longer committed, but the reasoning survives the change: provisioning should not
write to a file the harness owns and rewrites on its own schedule, and
`pi install` would fight `pi-setup` over the same array.

`pi update --extensions` does not write to `settings.json`. It reads the
`packages` array already there and installs whatever is declared but absent
from disk.

This was verified experimentally, not assumed. With both `~/.pi/agent/npm`
and `~/.pi/agent/git` moved aside — removing every package of both source
types from disk — a single `pi update --extensions` run restored all of them:
`npm:`-sourced packages reappeared under `~/.pi/agent/npm/node_modules/`, and
the `git:`-sourced package was freshly cloned (`Cloning into
'~/.pi/agent/git/github.com/obra/superpowers'...`) with its full
payload present, not an empty directory — confirmed by listing its `skills/`
subdirectory and finding all fourteen expected entries. `settings.json`
stayed untouched (`git status --short` clean) throughout. Verified against pi
0.84.2.

## Consequences

Add or remove a pi package by editing `plugins.yaml`, not by running
`pi install`. A manual `pi install` still works, but `pi-setup` owns the
`packages` array and will drop anything not declared in the manifest on the next
provisioning run. Everything else in `settings.json` is pi's own and is
preserved, so the preferences pi writes there survive.

`pi-setup` must run before `pi-install-plugins` in the `setup_ai` chain, or
reconciliation reads a `packages` array that predates the manifest.

Not re-verified since 2026-08-18; a pi upgrade should be re-tested rather
than assumed compatible, since this behaviour is not documented upstream.
