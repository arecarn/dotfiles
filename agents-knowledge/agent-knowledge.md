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
| Claude Code | `agents/bin/agent-knowledge-session-start`, registered in settings for `SessionStart` and `SubagentStart` |
| OpenCode | `opencode/.config/opencode/plugins/agent-knowledge.ts` |

# Rules that are easy to break

Only root indexes reach a model; concepts are read on request. Model-facing
output never names a bundle path -- only `status` does, and that is local.

A harness adapter must cover subagents as well as sessions, which is a separate
moment in every harness: pi hooks `before_agent_start`, OpenCode transforms each
model request, and Claude Code needs `SubagentStart` alongside `SessionStart`.
Cover only the session and a subagent silently falls back to whatever pointer
the project's instructions carry -- which reaches no bundle outside the repo.

See docs/adr/0005-resolve-agent-knowledge-once-in-a-shared-cli.md.

# Checking a bundle

`agent-knowledge check` reports structural drift -- dead links, unreachable
documents, missing frontmatter, an entry that no longer matches its document's
own description. `--path DIR` checks one bundle wherever it lives, which is how
a private bundle with no CI of its own gets checked. `inv lint-bundles` runs the
same code over this repo's bundles.

It checks structure, not truth, and not whether an entry still matches the tasks
people bring -- `tests/knowledge_routing/` measures that with cold agents.

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
