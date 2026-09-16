"""Tests for the shared superpowers-bootstrap flag.

Covers manage/superpowers_toggle.py (the flag itself), the CLI wrapper, and the
Claude Code hook that reads it. The pi side is covered separately in
tests/superpowers-toggle.test.ts, since pi extensions are TypeScript.
"""

# Test names document each case.
# pylint: disable=missing-function-docstring

import io
import json

from manage import superpowers_toggle
from manage.superpowers_toggle_cli import main as cli_main
from manage.superpowers_toggle_hooks import session_start


def test_an_untouched_state_dir_is_enabled(tmp_path):
    assert superpowers_toggle.is_enabled(tmp_path) is True


def test_setting_disabled_persists(tmp_path):
    superpowers_toggle.set_enabled(False, tmp_path)

    assert superpowers_toggle.is_enabled(tmp_path) is False


def test_setting_enabled_removes_the_flag_file(tmp_path):
    """An untouched install stays fileless, so re-enabling restores that state
    exactly rather than leaving a stray "on" marker behind."""
    superpowers_toggle.set_enabled(False, tmp_path)
    superpowers_toggle.set_enabled(True, tmp_path)

    assert not (tmp_path / "superpowers-bootstrap").exists()
    assert superpowers_toggle.is_enabled(tmp_path) is True


def test_state_dir_prefers_an_explicit_path(tmp_path, monkeypatch):
    monkeypatch.delenv(superpowers_toggle.STATE_DIR_ENV, raising=False)

    assert superpowers_toggle.state_dir(tmp_path) == tmp_path


def test_state_dir_falls_back_to_the_env_var(tmp_path, monkeypatch):
    monkeypatch.setenv(superpowers_toggle.STATE_DIR_ENV, str(tmp_path))

    assert superpowers_toggle.state_dir() == tmp_path


# --- CLI ---------------------------------------------------------------------


def _run_cli(capsys, *args):
    code = cli_main(list(args))
    return code, json.loads(capsys.readouterr().out)


def test_cli_status_defaults_to_enabled(tmp_path, capsys):
    code, payload = _run_cli(capsys, "status", "--state-dir", str(tmp_path))

    assert code == 0
    assert payload == {"enabled": True}


def test_cli_off_then_status_reports_disabled(tmp_path, capsys):
    _run_cli(capsys, "off", "--state-dir", str(tmp_path))
    code, payload = _run_cli(capsys, "status", "--state-dir", str(tmp_path))

    assert code == 0
    assert payload == {"enabled": False}


def test_cli_toggle_flips_from_enabled(tmp_path, capsys):
    code, payload = _run_cli(capsys, "toggle", "--state-dir", str(tmp_path))

    assert code == 0
    assert payload == {"enabled": False}


def test_cli_toggle_flips_back(tmp_path, capsys):
    _run_cli(capsys, "toggle", "--state-dir", str(tmp_path))
    code, payload = _run_cli(capsys, "toggle", "--state-dir", str(tmp_path))

    assert code == 0
    assert payload == {"enabled": True}


# --- Claude Code hook ----------------------------------------------------------


def _run_hook(state_dir):
    out = io.StringIO()
    code = session_start(stdin=io.StringIO("{}"), stdout=out, state_dir=state_dir)
    return code, json.loads(out.getvalue())


def test_hook_emits_nothing_when_enabled(tmp_path):
    code, payload = _run_hook(tmp_path)

    assert code == 0
    assert payload == {}


def test_hook_emits_a_disregard_note_when_disabled(tmp_path):
    superpowers_toggle.set_enabled(False, tmp_path)

    code, payload = _run_hook(tmp_path)

    assert code == 0
    assert payload["hookSpecificOutput"]["hookEventName"] == "SessionStart"
    assert "off" in payload["hookSpecificOutput"]["additionalContext"]


def test_hook_tolerates_unparseable_stdin(tmp_path):
    out = io.StringIO()
    code = session_start(stdin=io.StringIO("not json"), stdout=out, state_dir=tmp_path)

    assert code == 0
    assert json.loads(out.getvalue()) == {}
