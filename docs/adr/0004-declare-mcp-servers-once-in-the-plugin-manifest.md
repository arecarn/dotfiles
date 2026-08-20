# Declare each MCP server once in the plugin manifest

`agents/.config/ai-skills/plugins.yaml` (plus `plugins_local.yaml` from a
`dotfiles_local` repo) is the only place an MCP server is declared.
`uv run inv install-mcp` writes those declarations into each harness's own MCP
config file: `~/.claude.json` for Claude Code, `~/.agents/mcp.json` for pi.

## Why

Every harness reads a different file, and none of them reads another's, so a
server has to appear in as many files as there are harnesses. Hand-maintaining
those copies had already gone wrong: this repo declared three servers in both
`plugins.yaml` and a stowed `agents/.config/mcp/mcp.json`, another nine existed
only in `~/.claude.json` — a file nothing versions — leaving pi without them, and
a third copy in a `dotfiles_local` opencode config had drifted to a different
credential variable and a different server parameter for servers it shared with
Claude Code.

Generating from one declaration removes the copies a person has to keep in sync.
The stowed `agents/.config/mcp/mcp.json` is gone: its three servers are in
`plugins.yaml`, and `inv clean-stow` removes the dead link left in
`~/.config/mcp/` on machines that stowed the old file.

## Consequences

The two writes are not symmetrical, because the files differ in ownership:

- `~/.claude.json` is **amended**. Claude Code creates it and keeps its entire
  state there, so only missing servers are added; an edited declaration does not
  propagate, and changing an existing server there is a manual edit (or delete
  the entry and re-run). An absent file stays absent rather than gaining a stub
  before Claude Code's first run.
- `~/.agents/mcp.json` is **generated whole**, so edits and removals propagate.
  That path is one of several global configs pi-mcp-adapter merges, and the only
  one it never writes to itself — its `/mcp` panel writes `~/.pi/agent/mcp.json`,
  which is deliberately left alone so a server added interactively survives
  provisioning.

pi's MCP config now arrives from `inv install-mcp` (a `setup-ai` dependency)
rather than from `inv stow`.

Credentials stay out of the manifest as `${ENV_VAR}` references, which both
harnesses expand at connect time. Work servers are declared in
`plugins_local.yaml`, keeping internal hostnames out of this public repo.

opencode still keeps its own MCP block in `dotfiles_local`: its schema differs
(`type: remote`, `oauth: false`), so folding it in needs a translation step that
this change does not attempt.

Verified on 2026-08-20 against pi 0.84.2 and pi-mcp-adapter by loading the
generated file through the adapter's own `loadMcpConfig`, which reported all
twelve servers from `~/.agents/mcp.json` with no source conflicts, and then
connecting one of them from a fresh `pi` run. A pi upgrade should be re-checked
rather than assumed: which paths the adapter reads and which it writes are its
choices, not documented guarantees.
