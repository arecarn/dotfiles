# Provisioning fails in CI on tasks that pass on every desktop

**CI runners have no desktop session, so any Ansible task touching a GNOME unit
or a desktop-only system package fails there while succeeding on every machine
you actually use.**

Gating on `os_family` is not enough — the runner is the same OS family as the
desktop, it simply has no session. Gate desktop-only tasks with
`failed_when: false` instead; `ansible/tasks/os-baseline.yml` has the worked
examples.

This is the headless half of a wider trap: provisioning behaves differently on a
bare runner than on a developed machine. The other half is
[lint passing locally proving nothing about CI](lint-passing-locally-proves-nothing-about-ci.md).

**Confirmed:** unknown, predates this convention — migrated from `AGENTS.md`.
