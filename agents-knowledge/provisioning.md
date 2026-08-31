---
type: Playbook
title: Provisioning
description: Adding an Ansible task file, and the two ways a new task passes locally but fails on a headless or bare machine
---
# Adding a tool

Add a task file in `ansible/tasks/`, then add an
`ansible.builtin.import_tasks` line for it to the `tasks:` list in
`ansible/site.yml`. A task file that nothing imports is never run, and
provisioning still succeeds -- so the omission is silent.

Tag anything desktop-only with `desktop-only`, as `os-baseline.yml` and
`wezterm.yml` do.

# Inventory

Managed in `ansible/hosts`. Local provisioning uses `--inventory localhost`.

# Two machines your machine is not

Gate desktop-only tasks with `failed_when: false` rather than `os_family`, or
they fail on headless CI -- see
docs/gotchas/desktop-only-ansible-tasks-fail-on-ci.md.

A new install task's first-run path only executes on a bare machine, so
simulate one locally (`HOME=/tmp/fakehome ansible-playbook ...`) rather than
paying a CI round per missing prerequisite -- see
docs/gotchas/first-run-install-paths-only-execute-on-a-bare-machine.md.
