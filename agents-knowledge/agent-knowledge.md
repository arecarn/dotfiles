---
type: Reference
title: The agent-knowledge integration
description: Where the resolver, CLI, and three adapters live in this repo
---
# Layout

| Piece | Path |
|-------|------|
| Resolver | `manage/knowledge/` |
| CLI | `scripts/bin/agent-knowledge` |
| pi | `pi/.pi/agent/extensions/agent-knowledge/` |
| Claude Code | `scripts/bin/agent-knowledge-session-start`, registered in settings |
| OpenCode | `opencode/.config/opencode/plugins/agent-knowledge.ts` |

# Rules that are easy to break

Only root indexes reach a model; concepts are read on request. Model-facing
output never names a bundle path -- only `status` does, and that is local.

See docs/adr/0005-resolve-agent-knowledge-once-in-a-shared-cli.md.
