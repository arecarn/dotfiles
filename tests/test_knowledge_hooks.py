"""Tests for the Claude Code SessionStart hook.

The hook's contract is narrow but easy to get wrong: put the catalog in Claude's
additionalContext field, keep bundle paths out of it, and never fail the session.
"""

# Test names document each case, and the helpers are private to the module.
# pylint: disable=missing-function-docstring

import io
import json

from manage.knowledge import hooks

INDEX = """\
---
okf_version: "0.2"
---
# Index

* [Ops](ops.md) - operations
"""


def _bundle(root):
    root.mkdir(parents=True, exist_ok=True)
    (root / "index.md").write_text(INDEX, encoding="utf-8")
    return root


def _config(tmp_path, bundle_root):
    config_dir = tmp_path / "config"
    config_dir.mkdir(exist_ok=True)
    (config_dir / "bundles.yaml").write_text(
        "version: 1\n"
        "bundles:\n"
        "  - id: personal\n"
        "    name: Personal knowledge\n"
        "    description: General references\n"
        f"    path: {bundle_root}\n"
        "    activate:\n"
        "      always: true\n",
        encoding="utf-8",
    )
    return config_dir


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


def test_no_active_bundles_produces_no_context(tmp_path):
    code, payload = _run(tmp_path / "none", {"cwd": str(tmp_path)})

    assert (code, payload) == (0, {})


def test_the_hook_resolves_the_directory_claude_reports(tmp_path):
    """Claude may invoke the hook from elsewhere, so `cwd` comes from the event."""
    work = tmp_path / "work"
    work.mkdir()
    config_dir = _config(tmp_path, _bundle(tmp_path / "kb"))
    (config_dir / "bundles.yaml").write_text(
        (config_dir / "bundles.yaml")
        .read_text(encoding="utf-8")
        .replace("      always: true\n", f"      roots:\n        - {work}\n"),
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
    (config_dir / "bundles.yaml").write_text("version: 4\n", encoding="utf-8")

    code, payload = _run(config_dir, {"cwd": str(tmp_path)})

    assert (code, payload) == (0, {})


def test_malformed_hook_input_does_not_fail_the_session(tmp_path):
    out = io.StringIO()

    code = hooks.session_start(
        stdin=io.StringIO("not json"), stdout=out, config_dir=tmp_path / "none"
    )

    assert (code, json.loads(out.getvalue())) == (0, {})
