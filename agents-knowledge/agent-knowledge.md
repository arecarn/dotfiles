---
type: Reference
title: The agent-knowledge integration
description: Where the resolver, CLI, and the three harness adapters live, the two rules that are easy to break, and when a bundle needs no tooling at all
---
# Layout

| Piece | Path |
|-------|------|
| Resolver | `manage/knowledge/` |
| CLI | `agents/bin/agent-knowledge` |
| pi | `pi/.pi/agent/extensions/agent-knowledge/` |
| Claude Code | `agents/bin/agent-knowledge-session-start`, registered in settings |
| OpenCode | `opencode/.config/opencode/plugins/agent-knowledge.ts` |

# Rules that are easy to break

Only root indexes reach a model; concepts are read on request. Model-facing
output never names a bundle path -- only `status` does, and that is local.

See docs/adr/0005-resolve-agent-knowledge-once-in-a-shared-cli.md.

# None of this is a precondition

A bundle is Markdown in a directory, so an agent with a read tool can use one
knowing only that the directory exists. A pointer in `AGENTS.md` is the whole
integration, and pi's extension falls back to reading `agents-knowledge/index.md`
itself when the CLI does not answer.

The CLI earns its place on three things a pointer cannot do: bundles that live
outside the workspace, activation rules that keep a work bundle out of unrelated
sessions, and disclosure at session start rather than trusting the agent to go
looking. A single project bundle needs none of them. Reach for the tooling when a
bundle must be found from outside the repo or must stay silent somewhere -- not
to set one up.
