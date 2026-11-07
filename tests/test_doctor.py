"""Tests for finding commands in Claude Code's settings that no longer exist."""

# Test names document each case.
# pylint: disable=missing-function-docstring

import json

from manage.agents import doctor


def _write_settings(home, settings):
    path = home / ".claude" / "settings.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(settings))


def _hook(command):
    return {"hooks": [{"type": "command", "command": command}]}


def test_an_absent_settings_file_has_no_problems(tmp_path):
    assert doctor.missing_claude_commands(tmp_path) == []


def test_a_hook_whose_script_exists_is_fine(tmp_path):
    script = tmp_path / "hook.py"
    script.write_text("")
    _write_settings(tmp_path, {"hooks": {"Stop": [_hook(f"python3 {script}")]}})

    assert doctor.missing_claude_commands(tmp_path) == []


def test_a_hook_whose_script_is_gone_is_reported_with_its_event(tmp_path):
    gone = tmp_path / "gone.py"
    _write_settings(tmp_path, {"hooks": {"SessionEnd": [_hook(f"python3 {gone}")]}})

    problems = doctor.missing_claude_commands(tmp_path)

    assert len(problems) == 1
    assert "SessionEnd" in problems[0]
    assert str(gone) in problems[0]


def test_the_status_line_command_is_checked_too(tmp_path):
    gone = tmp_path / "statusline.py"
    _write_settings(
        tmp_path, {"statusLine": {"type": "command", "command": f"python3 {gone}"}}
    )

    assert "statusLine" in doctor.missing_claude_commands(tmp_path)[0]


def test_a_variable_path_is_skipped_because_it_resolves_at_run_time(tmp_path):
    _write_settings(
        tmp_path, {"hooks": {"Stop": [_hook('"${CLAUDE_PLUGIN_ROOT}/hooks/start"')]}}
    )

    assert doctor.missing_claude_commands(tmp_path) == []


def test_bare_commands_without_a_path_are_skipped(tmp_path):
    _write_settings(tmp_path, {"hooks": {"Stop": [_hook("python3 -m something")]}})

    assert doctor.missing_claude_commands(tmp_path) == []


def test_report_says_nothing_when_there_are_no_problems(capsys):
    assert doctor.report([]) is False
    assert capsys.readouterr().out == ""


def test_report_names_each_problem_and_the_fix(capsys):
    assert doctor.report(["hook Stop runs /x, which does not exist"]) is True

    out = capsys.readouterr().out
    assert "/x" in out
    assert "removed-hook cleanup" in out
