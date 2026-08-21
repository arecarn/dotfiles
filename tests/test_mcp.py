"""Tests for registering the manifest's MCP servers with each harness.

The two config files are written differently because they differ in ownership,
not because the harnesses differ (ADR-0004). These pin that difference: the
Claude Code file is amended and never created, pi's is generated whole.
"""

# Test names document each case, and the helpers are private to the module.
# pylint: disable=missing-function-docstring,protected-access

import json

import pytest

from manage.agents import mcp, plugins

SERVERS = {
    "ticktick": {"type": "http", "url": "https://example.test/tt"},
    "gmail": {"type": "http", "url": "https://example.test/gm"},
}


@pytest.fixture(name="home")
def fixture_home(tmp_path, monkeypatch):
    """A fake $HOME with the manifest stubbed to two MCP servers."""
    manifest = plugins.Manifest({name: {"mcp": cfg} for name, cfg in SERVERS.items()})
    monkeypatch.setattr(plugins, "load", lambda: manifest)
    return tmp_path


def _claude(home):
    return home / ".claude.json"


def _pi(home):
    return home / ".agents" / "mcp.json"


# --- the file Claude Code owns -----------------------------------------------


def test_an_absent_claude_config_is_left_absent(home):
    mcp.register(home)

    assert not _claude(home).exists()


def test_servers_are_added_to_an_existing_claude_config(home):
    _claude(home).write_text(json.dumps({"mcpServers": {}}))

    mcp.register(home)

    assert set(json.loads(_claude(home).read_text())["mcpServers"]) == set(SERVERS)


def test_claude_keys_outside_mcp_servers_are_preserved(home):
    _claude(home).write_text(json.dumps({"userID": "abc", "mcpServers": {}}))

    mcp.register(home)

    assert json.loads(_claude(home).read_text())["userID"] == "abc"


def test_an_existing_server_definition_is_not_overwritten(home):
    mine = {"type": "http", "url": "https://edited-by-hand.test/"}
    _claude(home).write_text(json.dumps({"mcpServers": {"ticktick": mine}}))

    mcp.register(home)

    written = json.loads(_claude(home).read_text())["mcpServers"]
    assert written["ticktick"] == mine
    assert "gmail" in written


def test_a_claude_config_without_an_mcp_servers_key_gains_one(home):
    _claude(home).write_text(json.dumps({"userID": "abc"}))

    mcp.register(home)

    assert set(json.loads(_claude(home).read_text())["mcpServers"]) == set(SERVERS)


def test_amend_reports_nothing_added_when_every_server_is_present(home):
    _claude(home).write_text(json.dumps({"mcpServers": dict(SERVERS)}))

    assert mcp._amend(_claude(home), SERVERS) == []


# --- the file pi does not write ----------------------------------------------


def test_the_pi_config_is_created_when_absent(home):
    mcp.register(home)

    assert set(json.loads(_pi(home).read_text())["mcpServers"]) == set(SERVERS)


def test_a_removed_manifest_entry_propagates_to_the_pi_config(home):
    _pi(home).parent.mkdir(parents=True)
    _pi(home).write_text(json.dumps({"mcpServers": {"gone": {"type": "http"}}}))

    mcp.register(home)

    assert "gone" not in json.loads(_pi(home).read_text())["mcpServers"]


def test_rewriting_an_unchanged_pi_config_reports_no_change(home):
    mcp.register(home)

    assert mcp._write_config(_pi(home), SERVERS) is False


def test_registering_twice_is_stable(home):
    _claude(home).write_text(json.dumps({"mcpServers": {}}))

    mcp.register(home)
    first = _claude(home).read_text(), _pi(home).read_text()
    mcp.register(home)

    assert (_claude(home).read_text(), _pi(home).read_text()) == first


# --- nothing to register -----------------------------------------------------


def test_an_empty_manifest_writes_nothing(tmp_path, monkeypatch):
    monkeypatch.setattr(plugins, "load", lambda: plugins.Manifest({}))
    (tmp_path / ".claude.json").write_text(json.dumps({"mcpServers": {}}))

    mcp.register(tmp_path)

    assert json.loads((tmp_path / ".claude.json").read_text())["mcpServers"] == {}
    assert not (tmp_path / ".agents" / "mcp.json").exists()
