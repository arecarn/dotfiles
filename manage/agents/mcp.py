"""Registering the manifest's MCP servers with every harness that reads one.

One manifest entry per server feeds both harnesses, so neither drifts from the
declaration. See docs/adr/0004-declare-mcp-servers-once-in-the-plugin-manifest.md.
"""

import json
import pathlib

from manage.agents import plugins

# Claude Code creates this and keeps its whole state in it, so it is amended.
_CLAUDE_CONFIG = pathlib.PurePath(".claude.json")

# One of the global paths pi-mcp-adapter merges, and the only one it never
# writes to itself -- its /mcp panel writes ~/.pi/agent/mcp.json, left free for
# exactly that -- so this one can be generated whole.
_PI_CONFIG = pathlib.PurePath(".agents/mcp.json")


def _home(home):
    return pathlib.Path.home() if home is None else pathlib.Path(home)


def _amend(config_path, servers):
    """Add missing servers to a harness-owned config; return the names added.

    For a file the harness itself creates and writes far more than MCP config
    into. Existing entries are left untouched, so a server whose definition
    changed here has to be edited in that file by hand. An absent file stays
    absent: a stub written before the harness's first run would be a config file
    it never asked for.
    """
    if not config_path.exists():
        return []

    config = json.loads(config_path.read_text())
    config.setdefault("mcpServers", {})
    added = [name for name in servers if name not in config["mcpServers"]]
    if not added:
        return []

    for name in added:
        config["mcpServers"][name] = servers[name]
    config_path.write_text(json.dumps(config, indent=2) + "\n")
    return added


def _write_config(config_path, servers):
    """Generate a whole config file; return True if it changed.

    Unlike `_amend` this owns the file outright, so an edited or removed
    manifest entry propagates. Only for a path no harness writes to itself, or
    the harness's own writes get discarded on the next provisioning run.
    """
    content = json.dumps({"mcpServers": servers}, indent=2) + "\n"
    if config_path.exists() and config_path.read_text() == content:
        return False

    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(content)
    return True


def register(home=None):
    """Write the manifest's MCP servers into each harness's own config file.

    The two are written differently because the files differ in ownership, not
    because the harnesses differ; see the constants above.
    """
    servers = plugins.load().mcp_servers()
    if not servers:
        return

    home = _home(home)

    claude_json = home / _CLAUDE_CONFIG
    added = _amend(claude_json, servers)
    if added:
        print(f"Added MCP servers to {claude_json}: {', '.join(added)}")
        print("Run /mcp in Claude Code to authorize any of them that use OAuth.")

    pi_config = home / _PI_CONFIG
    if _write_config(pi_config, servers):
        print(f"Wrote {len(servers)} MCP servers to {pi_config}")
