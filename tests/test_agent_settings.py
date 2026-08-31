"""Tests for writing this repo's declarations into each harness's settings file."""

# Test names document each case; the module under test exposes these helpers
# privately and the tests are their only caller.
# pylint: disable=missing-function-docstring,protected-access

import json
import pathlib

import pytest
from ruamel.yaml import YAML

from manage.agents import plugins, settings


@pytest.fixture(name="pi_home")
def fixture_pi_home(tmp_path, monkeypatch):
    """A fake $HOME, with the manifest stubbed to two pi packages.

    The home is passed explicitly rather than patched, so these exercise the
    same call shape tasks.py uses.
    """
    manifest = plugins.Manifest({
        "a": {"pi_package": "git:github.com/a/b"},
        "c": {"pi_package": "npm:c"},
    })
    monkeypatch.setattr(plugins, "load", lambda: manifest)
    return tmp_path


def _settings(home):
    return json.loads((home / ".pi" / "agent" / "settings.json").read_text())


def test_creates_the_file_when_absent(pi_home):
    settings.setup_pi(pi_home)
    assert _settings(pi_home)["packages"] == ["git:github.com/a/b", "npm:c"]


def test_preserves_keys_pi_wrote_itself(pi_home):
    path = pi_home / ".pi" / "agent" / "settings.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps({"theme": "dark", "defaultModel": "some-model"}))

    settings.setup_pi(pi_home)

    written = _settings(pi_home)
    assert written["theme"] == "dark"
    assert written["defaultModel"] == "some-model"


def test_applies_private_settings_overrides(pi_home):
    local = pi_home / ".config" / "ai-skills" / "pi-settings.local.json"
    local.parent.mkdir(parents=True)
    local.write_text(
        json.dumps({"defaultProvider": "litellm", "defaultModel": "gpt-5.6-sol"})
    )

    settings.setup_pi(pi_home)

    written = _settings(pi_home)
    assert written["defaultProvider"] == "litellm"
    assert written["defaultModel"] == "gpt-5.6-sol"
    assert written["packages"] == ["git:github.com/a/b", "npm:c"]


def test_a_dropped_declaration_is_removed(pi_home, monkeypatch):
    path = pi_home / ".pi" / "agent" / "settings.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps({"packages": ["npm:gone", "npm:c"]}))

    manifest = plugins.Manifest({"c": {"pi_package": "npm:c"}})
    monkeypatch.setattr(plugins, "load", lambda: manifest)
    settings.setup_pi(pi_home)

    assert _settings(pi_home)["packages"] == ["npm:c"]


def test_migrates_an_active_settings_symlink_to_a_real_file(pi_home):
    repo_file = pi_home / "repo" / "settings.json"
    repo_file.parent.mkdir(parents=True)
    repo_file.write_text(json.dumps({"theme": "dark", "lastChangelogVersion": "1.2.3"}))
    path = pi_home / ".pi" / "agent" / "settings.json"
    path.parent.mkdir(parents=True)
    path.symlink_to(repo_file)

    settings.setup_pi(pi_home)

    assert not path.is_symlink()
    assert _settings(pi_home)["theme"] == "dark"
    assert _settings(pi_home)["lastChangelogVersion"] == "1.2.3"
    assert json.loads(repo_file.read_text())["theme"] == "dark"


def test_replaces_a_stale_symlink_instead_of_writing_through_it(pi_home):
    repo_file = pi_home / "repo" / "settings.json"
    repo_file.parent.mkdir(parents=True)
    path = pi_home / ".pi" / "agent" / "settings.json"
    path.parent.mkdir(parents=True)
    path.symlink_to(repo_file)  # target does not exist, as after the file was removed

    settings.setup_pi(pi_home)

    assert not path.is_symlink()
    assert not repo_file.exists()
    assert _settings(pi_home)["packages"] == ["git:github.com/a/b", "npm:c"]


def test_the_committed_manifest_declares_the_expected_packages():
    """Guards the pi_package: keys in the manifest this repo ships.

    Reads the repo's own copy rather than calling _manifest_pi_packages(), which
    reads the stowed ~/.config/ai-skills/plugins.yaml and so would depend on
    whether the machine running the tests has been stowed.
    """
    manifest = YAML().load(pathlib.Path("agents/.config/ai-skills/plugins.yaml"))
    declared = [
        cfg["pi_package"]
        for cfg in manifest.values()
        if isinstance(cfg, dict) and "pi_package" in cfg
    ]
    assert declared == [
        "git:github.com/mattpocock/skills",
        "git:github.com/obra/superpowers",
        "npm:pi-subagents",
        "npm:pi-intercom",
        "npm:pi-mcp-adapter",
        "npm:pi-background-tasks",
    ]


# --- the file Claude Code owns -----------------------------------------------


def _claude_settings(home):
    return home / ".claude" / "settings.json"


def test_an_absent_claude_settings_file_is_created(tmp_path):
    """A fresh machine is exactly when these settings are wanted, so an absent
    file is created rather than skipped."""
    settings.setup_claude(tmp_path)

    assert json.loads(_claude_settings(tmp_path).read_text())["outputStyle"] == "Concise"


def test_the_claude_directory_is_created_when_absent(tmp_path):
    settings.setup_claude(tmp_path)

    assert _claude_settings(tmp_path).parent.is_dir()


def test_creating_then_rerunning_is_stable(tmp_path):
    settings.setup_claude(tmp_path)
    first = _claude_settings(tmp_path).read_text()
    settings.setup_claude(tmp_path)

    assert _claude_settings(tmp_path).read_text() == first


def test_the_output_style_is_set(tmp_path):
    _claude_settings(tmp_path).parent.mkdir(parents=True)
    _claude_settings(tmp_path).write_text(json.dumps({}))

    settings.setup_claude(tmp_path)

    assert json.loads(_claude_settings(tmp_path).read_text())["outputStyle"] == "Concise"


def test_keys_claude_wrote_itself_are_preserved(tmp_path):
    _claude_settings(tmp_path).parent.mkdir(parents=True)
    _claude_settings(tmp_path).write_text(json.dumps({"theme": "dark"}))

    settings.setup_claude(tmp_path)

    assert json.loads(_claude_settings(tmp_path).read_text())["theme"] == "dark"


def test_an_existing_permissions_block_keeps_its_other_keys(tmp_path):
    _claude_settings(tmp_path).parent.mkdir(parents=True)
    _claude_settings(tmp_path).write_text(
        json.dumps({"permissions": {"allow": ["Bash(ls:*)"]}})
    )

    settings.setup_claude(tmp_path)

    permissions = json.loads(_claude_settings(tmp_path).read_text())["permissions"]
    assert permissions["allow"] == ["Bash(ls:*)"]
    assert permissions["defaultMode"] == "bypassPermissions"


# --- the agent-knowledge hook -----------------------------------------------------


def _claude_hooks(home):
    return json.loads(_claude_settings(home).read_text()).get("hooks", {})


def _hook_commands(home, event):
    entries = _claude_hooks(home).get(event, [])
    return [h["command"] for entry in entries for h in entry["hooks"]]


def test_the_knowledge_hook_is_registered_for_claude(tmp_path):
    """Claude Code loads plugins from marketplace installs, not from a directory
    dropped into ~/.claude/plugins, so the hook is registered in settings."""
    settings.setup_claude(tmp_path)

    starts = _claude_hooks(tmp_path)["SessionStart"]
    commands = [h["command"] for entry in starts for h in entry["hooks"]]
    assert any("agent-knowledge" in command for command in commands)


def test_the_registered_hook_command_is_the_stowed_path(tmp_path):
    """An absolute path, because a hook has no shell and no PATH of ours."""
    settings.setup_claude(tmp_path)

    starts = _claude_hooks(tmp_path)["SessionStart"]
    commands = [h["command"] for entry in starts for h in entry["hooks"]]
    assert any(command.startswith(str(tmp_path)) for command in commands)


def test_hooks_other_tools_registered_are_left_alone(tmp_path):
    _claude_settings(tmp_path).parent.mkdir(parents=True)
    _claude_settings(tmp_path).write_text(
        json.dumps({"hooks": {"Stop": [{"matcher": "*", "hooks": []}]}})
    )

    settings.setup_claude(tmp_path)

    assert "Stop" in _claude_hooks(tmp_path)


def test_registering_the_hook_twice_does_not_duplicate_it(tmp_path):
    settings.setup_claude(tmp_path)
    settings.setup_claude(tmp_path)

    for event in ("SessionStart", "SubagentStart"):
        commands = _hook_commands(tmp_path, event)
        assert len([c for c in commands if "agent-knowledge" in c]) == 1


def test_the_knowledge_hook_is_registered_for_subagents(tmp_path):
    """A subagent gets its own context window and fires no SessionStart, so
    registering only that event leaves every subagent without a catalog."""
    settings.setup_claude(tmp_path)

    commands = _hook_commands(tmp_path, "SubagentStart")
    assert any("agent-knowledge" in command for command in commands)


def test_the_subagent_hook_matches_every_agent_type(tmp_path):
    """SubagentStart's matcher filters on agent type, and knowledge applies
    whatever the agent is."""
    settings.setup_claude(tmp_path)

    entries = _claude_hooks(tmp_path)["SubagentStart"]
    ours = [
        entry
        for entry in entries
        if any("agent-knowledge" in h["command"] for h in entry["hooks"])
    ]
    assert [entry["matcher"] for entry in ours] == ["*"]


def test_a_machine_registered_before_subagents_gains_the_new_event(tmp_path):
    """The SessionStart entry is already present on such a machine; it is not
    evidence that SubagentStart is."""
    _claude_settings(tmp_path).parent.mkdir(parents=True)
    command = str(tmp_path / "bin/agent-knowledge-session-start")
    _claude_settings(tmp_path).write_text(
        json.dumps(
            {
                "hooks": {
                    "SessionStart": [
                        {
                            "matcher": "startup|resume|clear|compact",
                            "hooks": [{"type": "command", "command": command}],
                        }
                    ]
                }
            }
        )
    )

    settings.setup_claude(tmp_path)

    assert _hook_commands(tmp_path, "SubagentStart") == [command]
    assert _hook_commands(tmp_path, "SessionStart") == [command]
