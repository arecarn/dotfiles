# `pi install`/`pi remove` leave a whitespace-only diff in `settings.json`

**After running `pi install <source>` or `pi remove <source>` by hand,
`git diff pi/.pi/agent/settings.json` shows a change even when the `packages`
array content is otherwise identical — the diff is just `\ No newline at end
of file` appearing or disappearing.**

`~/.pi/agent/settings.json` is a symlink into `pi/.pi/agent/settings.json`.
`pi install`/`pi remove` rewrite the file in place through the symlink (the
symlink itself survives, and key order and indentation are preserved), but
pi's writer does not emit a trailing newline. The committed file has one, so
the rewrite always drops it — a change that is easy to stage and commit
without noticing, since it carries no semantic content.

Provisioning does not hit this trap: `uv run inv pi-install-plugins` runs `pi
update --extensions`, which does not write to `settings.json`. Why
provisioning is built that way is recorded in
[docs/adr/0002-reconcile-pi-packages-instead-of-installing-per-package.md](../adr/0002-reconcile-pi-packages-instead-of-installing-per-package.md).

If the drift happens, `git checkout -- pi/.pi/agent/settings.json` restores
the exact committed bytes — no manual newline fix needed.

**Confirmed:** 2026-08-18, against pi 0.84.2.
