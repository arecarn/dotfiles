"""Tests for declaring pi packages in pi's own settings file."""

# Test names document each case; the module under test exposes these helpers
# privately and the tests are their only caller.
# pylint: disable=missing-function-docstring,protected-access

import json
import pathlib

import pytest

import tasks


@pytest.fixture(name="pi_home")
def fixture_pi_home(tmp_path, monkeypatch):
    """A fake $HOME, with the manifest stubbed to two pi packages."""
    monkeypatch.setattr(pathlib.Path, "home", classmethod(lambda cls: tmp_path))
    monkeypatch.setattr(
        tasks, "_manifest_pi_packages", lambda: ["git:github.com/a/b", "npm:c"]
    )
    return tmp_path


def _settings(home):
    return json.loads((home / ".pi" / "agent" / "settings.json").read_text())


def test_creates_the_file_when_absent(pi_home):
    tasks._setup_pi_settings()
    assert _settings(pi_home)["packages"] == ["git:github.com/a/b", "npm:c"]


def test_preserves_keys_pi_wrote_itself(pi_home):
    path = pi_home / ".pi" / "agent" / "settings.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps({"theme": "dark", "defaultModel": "some-model"}))

    tasks._setup_pi_settings()

    settings = _settings(pi_home)
    assert settings["theme"] == "dark"
    assert settings["defaultModel"] == "some-model"


def test_a_dropped_declaration_is_removed(pi_home, monkeypatch):
    path = pi_home / ".pi" / "agent" / "settings.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps({"packages": ["npm:gone", "npm:c"]}))

    monkeypatch.setattr(tasks, "_manifest_pi_packages", lambda: ["npm:c"])
    tasks._setup_pi_settings()

    assert _settings(pi_home)["packages"] == ["npm:c"]


def test_replaces_a_stale_symlink_instead_of_writing_through_it(pi_home):
    repo_file = pi_home / "repo" / "settings.json"
    repo_file.parent.mkdir(parents=True)
    path = pi_home / ".pi" / "agent" / "settings.json"
    path.parent.mkdir(parents=True)
    path.symlink_to(repo_file)  # target does not exist, as after the file was removed

    tasks._setup_pi_settings()

    assert not path.is_symlink()
    assert not repo_file.exists()
    assert _settings(pi_home)["packages"] == ["git:github.com/a/b", "npm:c"]


def test_declared_packages_come_from_the_manifest():
    """The real manifest declares the three packages this repo expects."""
    assert tasks._manifest_pi_packages() == [
        "git:github.com/obra/superpowers",
        "npm:pi-subagents",
        "npm:pi-mcp-adapter",
    ]
