---
type: Reference
title: MCP servers
description: Adding or changing a server in the one manifest that feeds every harness, and where credentials may not go
---
# One declaration, many harnesses

MCP servers are declared once, in `agents/.config/ai-skills/plugins.yaml` (plus a
`dotfiles_local` repo's `plugins_local.yaml`). Its header comment carries the
schema for an `mcp:` block. `inv install-mcp` writes them into each harness's
own config file: `~/.claude.json` is amended, `~/.agents/mcp.json` is generated
whole for pi.

Add or change a server in the manifest, never in those generated files.

# Credentials

They belong in the manifest only as `${ENV_VAR}` references; the harness expands
them at connect time. The real secret goes in a `dotfiles_local` shell fragment,
never here.

`manage/agents/plugins.py` passes an `mcp:` block through verbatim, so the shape
must be whatever the harness expects. Every server declared so far is a remote
`type: http` one -- no stdio server exists yet, so `command`/`args`/`env` are
documented in the manifest header but unexercised.

`~/.claude.json` is only amended, so an entry that is already wrong there must be
removed by hand before re-running `inv install-mcp`.

See docs/adr/0004-declare-mcp-servers-once-in-the-plugin-manifest.md.
