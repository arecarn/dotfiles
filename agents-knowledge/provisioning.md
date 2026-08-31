---
type: Playbook
title: Provisioning
description: Adding a package or an Ansible task file, the Linux/Windows split that leaves a change half-done, the binary that is not named after its package, and why a failed install does not fail the run
---
# Adding a package

Most tools need no task file. `ansible/group_vars/all.yml` holds the lists that
`ansible/tasks/system-packages.yml` loops over. **Grep it first** -- a tool is
often already in the Linux lists and missing only from the Windows ones.

| List | For |
|------|-----|
| `common_system_packages` | same package name on Debian and RedHat |
| `os_family_system_packages` | different names per family (`Debian:` / `RedHat:`) |
| `desktop_only_system_packages` | everywhere except CI (see below) |
| `windows_system_packages` | Chocolatey |
| `windows_desktop_only_system_packages` | Chocolatey, except on a headless host |

**The Windows lists are read by `manage/provision.py`, not by Ansible.** Adding
to the Linux lists alone leaves Windows without the tool, and nothing reports
that the change was half-done.

Reach for a task file in `ansible/tasks/` only when the tool is not in the distro
repos or needs a pinned upstream release. Then add an
`ansible.builtin.import_tasks` line for it to the `tasks:` list in
`ansible/site.yml`: a task file that nothing imports is never run, provisioning
still succeeds, and the omission is silent.

Packages needing contrib, EPEL, or CRB need `ansible/tasks/package-repos.yml`
first.

# The binary is not always named after the package

Debian renames binaries that collide: `bat` installs as `batcat`, `fd-find` as
`fdfind`. The package installs fine and the command does not exist, on Debian
only -- invisible from a RedHat machine. `zsh/.config/zsh/aliases.zsh` carries
the compensating alias for `bat`; check whether a new tool needs one.

# A failed install does not fail the run

The package tasks run with `ignore_errors: true`. A wrong or renamed package
name surfaces only in the "Report system packages that failed to install" debug
task at the end of `system-packages.yml` -- easy to scroll past, and green CI
does not mean the package installed. A package task added *after* that report
task has its failures reported nowhere.

# Two different desktop-only mechanisms

They solve different problems and neither replaces the other.

**The `desktop-only` tag** excludes whole task files and the desktop package
list. `tasks.py:210` passes `--skip-tags desktop-only` **only when running in
CI**, so a headless non-CI machine installs them in full; the tag is not a
display check. `os-baseline.yml` and `wezterm.yml` carry it.

**`failed_when: false`** suppresses the error from a task that runs everywhere
but cannot succeed without a session -- systemd user units, as in
`os-baseline.yml`. The task still runs; only its failure is ignored. Gating on
`os_family` instead does not help, because CI is the same family with no
session. See docs/gotchas/desktop-only-ansible-tasks-fail-on-ci.md.

# Testing a new task file

A new install task's first-run path only executes on a bare machine, so a
package already present on your laptop reports `ok` whether its name is right or
not. Simulate a bare machine (`HOME=/tmp/fakehome ansible-playbook ...`) rather
than paying a CI round per missing prerequisite -- see
docs/gotchas/first-run-install-paths-only-execute-on-a-bare-machine.md.

A tool the linters call must also reach PATH in CI; `.github/workflows/ci.yml`
adds the npm prefix and `~/.cargo/bin` by hand.

# There is no inventory file

`ansible/` holds no `hosts`. `tasks.py` passes `--inventory localhost,` inline --
the trailing comma is the host-list form, not a filename.
