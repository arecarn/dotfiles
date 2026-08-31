"""Tests for the Claude Code SessionStart and SubagentStart hook.

The hook's contract is narrow but easy to get wrong: put the catalog in Claude's
additionalContext field, echo back the event that fired, keep bundle paths out
of it, and never fail the session.
"""

# Test names document each case, and the helpers are private to the module.
# pylint: disable=missing-function-docstring

import io
import json

from knowledge_fixtures import bundle as _bundle
from knowledge_fixtures import config_dir as _config

from manage.knowledge import hooks


def _run(config_dir, event):
    out = io.StringIO()
    code = hooks.session_start(
        stdin=io.StringIO(json.dumps(event)), stdout=out, config_dir=config_dir
    )
    return code, json.loads(out.getvalue())


def test_the_catalog_is_returned_as_claude_additional_context(tmp_path):
    config_dir = _config(tmp_path, _bundle(tmp_path / "kb"))

    code, payload = _run(config_dir, {"cwd": str(tmp_path), "session_id": "s1"})

    assert code == 0
    assert payload["hookSpecificOutput"]["hookEventName"] == "SessionStart"
    assert "operations" in payload["hookSpecificOutput"]["additionalContext"]


def test_a_subagent_gets_the_catalog_under_its_own_event_name(tmp_path):
    """A subagent gets a fresh context window and fires no SessionStart, so
    without this it sees no catalog. Claude matches the reply against the event
    it fired, so the name must be echoed back rather than hardcoded."""
    config_dir = _config(tmp_path, _bundle(tmp_path / "kb"))

    code, payload = _run(
        config_dir,
        {
            "cwd": str(tmp_path),
            "hook_event_name": "SubagentStart",
            "agent_type": "Explore",
        },
    )

    assert code == 0
    assert payload["hookSpecificOutput"]["hookEventName"] == "SubagentStart"
    assert "operations" in payload["hookSpecificOutput"]["additionalContext"]


def test_an_unrecognised_event_name_falls_back_to_session_start(tmp_path):
    """The event name is echoed from input, so it is not trusted verbatim."""
    config_dir = _config(tmp_path, _bundle(tmp_path / "kb"))

    _, payload = _run(
        config_dir, {"cwd": str(tmp_path), "hook_event_name": "Nonsense"}
    )

    assert payload["hookSpecificOutput"]["hookEventName"] == "SessionStart"


def test_no_active_bundles_produces_no_context(tmp_path):
    code, payload = _run(tmp_path / "none", {"cwd": str(tmp_path)})

    assert (code, payload) == (0, {})


def test_the_hook_resolves_the_directory_claude_reports(tmp_path):
    """Claude may invoke the hook from elsewhere, so `cwd` comes from the event."""
    work = tmp_path / "work"
    work.mkdir()
    config_dir = _config(tmp_path, _bundle(tmp_path / "kb"))
    (config_dir / "config.yaml").write_text(
        "version: 1\nscopes:\n"
        "  - id: personal\n"
        "    activate:\n"
        f"      roots:\n        - {work}\n",
        encoding="utf-8",
    )

    _, outside = _run(config_dir, {"cwd": str(tmp_path)})
    _, inside = _run(config_dir, {"cwd": str(work)})

    assert outside == {}
    assert "operations" in inside["hookSpecificOutput"]["additionalContext"]


def test_bundle_paths_are_not_disclosed_to_the_model(tmp_path):
    root = _bundle(tmp_path / "kb")
    config_dir = _config(tmp_path, root)

    _, payload = _run(config_dir, {"cwd": str(tmp_path)})

    assert str(root) not in payload["hookSpecificOutput"]["additionalContext"]


def test_a_broken_configuration_does_not_fail_the_session(tmp_path):
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "config.yaml").write_text("version: 4\n", encoding="utf-8")

    code, payload = _run(config_dir, {"cwd": str(tmp_path)})

    assert (code, payload) == (0, {})


def test_malformed_hook_input_does_not_fail_the_session(tmp_path):
    out = io.StringIO()

    code = hooks.session_start(
        stdin=io.StringIO("not json"), stdout=out, config_dir=tmp_path / "none"
    )

    assert (code, json.loads(out.getvalue())) == (0, {})
