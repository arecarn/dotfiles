---
type: Reference
title: MCP servers
description: Adding or changing an MCP server -- the one manifest that feeds every harness, and where credentials may not go
---
# One declaration, many harnesses

MCP servers are declared once, in `plugins.yaml` (plus a `dotfiles_local`
repo's `plugins_local.yaml`). `inv install-mcp` writes them into each harness's
own config file: `~/.claude.json` is amended, `~/.agents/mcp.json` is generated
whole for pi.

Add or change a server in the manifest, never in those generated files.

# Credentials

They belong in the manifest only as `${ENV_VAR}` references.

See docs/adr/0004-declare-mcp-servers-once-in-the-plugin-manifest.md.
