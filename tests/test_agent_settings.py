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


def test_a_dropped_declaration_is_removed(pi_home, monkeypatch):
    path = pi_home / ".pi" / "agent" / "settings.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps({"packages": ["npm:gone", "npm:c"]}))

    manifest = plugins.Manifest({"c": {"pi_package": "npm:c"}})
    monkeypatch.setattr(plugins, "load", lambda: manifest)
    settings.setup_pi(pi_home)

    assert _settings(pi_home)["packages"] == ["npm:c"]


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
        "git:github.com/obra/superpowers",
        "npm:pi-subagents",
        "npm:pi-mcp-adapter",
    ]


# --- the file Claude Code owns -----------------------------------------------


def _claude_settings(home):
    return home / ".claude" / "settings.json"


def test_an_absent_claude_settings_file_is_left_absent(tmp_path):
    settings.setup_claude(tmp_path)

    assert not _claude_settings(tmp_path).exists()


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
