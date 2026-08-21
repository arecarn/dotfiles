# `inv stow` fails with WinError 1314 on Windows

**Creating a symlink on Windows is privilege-gated, so `inv stow` aborts with
`OSError: [WinError 1314] A required privilege is not held by the client`
unless the shell is elevated or Developer Mode is on.**

Nothing in the repo is wrong when this happens — the same command succeeds on
the same checkout from an elevated shell.

Either fix works:

- Run stow from an elevated shell. `gsudo uv run inv stow` is the convenient
  inline form, since `gsudo` is already on PATH.
- Enable Developer Mode once, under `Settings > For developers`.

Only *creating* a symlink needs the privilege. Symlinks that already exist keep
resolving without it, so a machine that was stowed once keeps working and the
failure only reappears when a new stow package is added.

The task layer tolerates this rather than failing: every stow-shaped task runs
inside `manage.stow.tolerating_windows_symlink_failure`, which prints a skip on
Windows and re-raises everywhere else. `inv stow-skills` is the deliberate
exception -- the fan-out is that task's whole result, so there the failure is
fatal.

CI works around this separately: the Windows job sets the
`AllowDevelopmentWithoutDevLicense` registry key and `git config --global
core.symlinks true` before stowing (see `.github/workflows/ci.yml`).

**Confirmed:** not re-verified as of 2026-08-09 — this review ran on Linux, and
the trap needs a Windows host to reproduce. What is current is the workaround:
CI's Windows job still sets `AllowDevelopmentWithoutDevLicense` before stowing
and passes. Whether stow would now fail without it is untested.
