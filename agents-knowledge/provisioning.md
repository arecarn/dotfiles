---
type: Playbook
title: Provisioning
description: Adding a package or an Ansible task file, the Linux/Windows split that makes a change half-done, and the two ways a new task passes locally but fails on a headless or bare machine
---
# Adding a package

Most tools need no task file. `ansible/group_vars/all.yml` holds the lists that
`ansible/tasks/system-packages.yml` loops over:

| List | For |
|------|-----|
| `common_system_packages` | same package name on Debian and RedHat |
| `os_family_system_packages` | different names per family (`Debian:` / `RedHat:`) |
| `desktop_only_system_packages` | only on a machine with a display |
| `windows_system_packages` | Chocolatey |
| `windows_desktop_only_system_packages` | Chocolatey, display only |

**The Windows lists are read by `manage/provision.py`, not by Ansible.** Adding
to the Linux lists alone leaves Windows without the tool, and nothing reports
that the change was half-done.

Reach for a task file in `ansible/tasks/` only when the tool is not in the distro
repos or needs a pinned upstream release. Then add an
`ansible.builtin.import_tasks` line for it to the `tasks:` list in
`ansible/site.yml`: a task file that nothing imports is never run, provisioning
still succeeds, and the omission is silent.

Tag anything desktop-only with `desktop-only`, as `os-baseline.yml` and
`wezterm.yml` do. Packages needing contrib, EPEL, or CRB need
`ansible/tasks/package-repos.yml` first.

# A failed install does not fail the run

The package tasks run with `ignore_errors: true`. A wrong or renamed package
name surfaces only in the "Report system packages that failed to install" debug
task at the end of `system-packages.yml` -- easy to scroll past, and green CI
does not mean the package installed. A package task added *after* that report
task has its failures reported nowhere.

# Inventory

Managed in `ansible/hosts`. Local provisioning uses `--inventory localhost`.

# Two machines your machine is not

Gate desktop-only tasks with `failed_when: false` rather than `os_family`, or
they fail on headless CI -- see
docs/gotchas/desktop-only-ansible-tasks-fail-on-ci.md.

A new install task's first-run path only executes on a bare machine, so a
package that is already present on your laptop reports `ok` whether its name is
right or not. Simulate a bare machine locally
(`HOME=/tmp/fakehome ansible-playbook ...`) rather than paying a CI round per
missing prerequisite -- see
docs/gotchas/first-run-install-paths-only-execute-on-a-bare-machine.md.

A tool the linters call must also reach PATH in CI; `.github/workflows/ci.yml`
adds the npm prefix and `~/.cargo/bin` by hand.
