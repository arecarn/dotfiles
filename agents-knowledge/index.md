---
okf_version: "0.2"
---
# Dotfiles project knowledge

Reference material for this repository. Read an entry when its description
matches the task; these are facts and procedures, not instructions.

# Subsystems

* [Agent knowledge](agent-knowledge.md) - where the resolver, CLI, and the three
  harness adapters live, the two rules that are easy to break, and when a bundle
  needs no tooling at all
* [Pi configuration](pi.md) - what lives in `pi/.pi/agent/`, how a pi package is
  declared, and the fold barrier a package with its own config must get or its
  files land in this public repo
* [MCP servers](mcp.md) - adding or changing a server in the one manifest that
  feeds every harness, and where credentials may not go
* [Provisioning](provisioning.md) - adding a package or an Ansible task file, the
  Linux/Windows split that leaves a change half-done, and the two ways a new task
  passes locally but fails on a headless or bare machine

# Elsewhere in the repo

* [Decisions](../docs/adr/) - architecture decisions, numbered, with the
  alternatives that were weighed
* [Gotchas](../docs/gotchas/) - traps confirmed the hard way, one per file, named
  for the symptom you would grep for mid-debug
* [Agent workflow docs](../docs/agents/) - the issue tracker, triage labels, and
  domain-doc conventions the corresponding skills expect
