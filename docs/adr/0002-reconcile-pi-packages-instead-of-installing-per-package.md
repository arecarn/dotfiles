# Reconcile pi packages via `pi update --extensions` instead of `pi install`

Pi packages are declared in the committed `packages` array in
`pi/.pi/agent/settings.json`. Provisioning (`uv run inv pi-install-plugins`)
reconciles installed packages against that array by running `pi update
--extensions`, rather than running `pi install <source>` once per declared
package.

## Why

`~/.pi/agent/settings.json` is a symlink into this repo, at
`pi/.pi/agent/settings.json`. `pi install <source>` writes to `settings.json`
whenever the source is not already in the `packages` array — that write lands
on a committed file, through the symlink, every time provisioning's declared
list and the currently-installed set differ.

`pi update --extensions` does not write to `settings.json`. It reads the
`packages` array already there and installs whatever is declared but absent
from disk.

This was verified experimentally, not assumed. With both `~/.pi/agent/npm`
and `~/.pi/agent/git` moved aside — removing every package of both source
types from disk — a single `pi update --extensions` run restored all of them:
`npm:`-sourced packages reappeared under `~/.pi/agent/npm/node_modules/`, and
the `git:`-sourced package was freshly cloned (`Cloning into
'/home/arecarn/.pi/agent/git/github.com/obra/superpowers'...`) with its full
payload present, not an empty directory — confirmed by listing its `skills/`
subdirectory and finding all fourteen expected entries. `settings.json`
stayed untouched (`git status --short` clean) throughout. Verified against pi
0.84.2.

## Consequences

`agents/.config/ai-skills/plugins.yaml` and the `packages` array in
`pi/.pi/agent/settings.json` both name pi packages, and nothing keeps them in
sync. `settings.json` is the list that actually drives installation via
`pi update --extensions`; `plugins.yaml`'s pi-related entries (where present)
are not consulted by `pi-install-plugins` and can drift without any check
catching it.

Manual `pi install`/`pi remove` runs remain the correct way to *change* the
declared package list — they are just not part of provisioning. Whatever they
write to `settings.json` becomes the new committed source of truth once
reviewed and committed normally. A `pi install`/`pi remove` run does drop the
file's trailing newline as a side effect; see
[docs/gotchas/pi-cli-drops-trailing-newline-in-settings-json.md](../gotchas/pi-cli-drops-trailing-newline-in-settings-json.md).

Not re-verified since 2026-08-18; a pi upgrade should be re-tested rather
than assumed compatible, since this behaviour is not documented upstream.
