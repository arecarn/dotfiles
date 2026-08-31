"""Tests for the CLI every harness adapter shells out to.

The adapters are the reason this is a process boundary: a Pi extension, a Claude
hook and an OpenCode plugin cannot import Python, so JSON on stdout is the one
contract all three share.
"""

# Test names document each case, and the helpers are private to the module.
# pylint: disable=missing-function-docstring

import ast
import json
import os
import subprocess
import sys

from knowledge_fixtures import bundle as _bundle
from knowledge_fixtures import config_dir as _config

CLI = "agents/bin/agent-knowledge"


def _run(repo_root, *args, cwd=None, config_dir=None):
    env = dict(os.environ, PYTHONPATH=str(repo_root))
    if config_dir is not None:
        env["AGENT_KNOWLEDGE_CONFIG_DIR"] = str(config_dir)
    return subprocess.run(
        [sys.executable, str(repo_root / CLI), *args],
        cwd=str(cwd or repo_root),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def _repo_root():
    import manage  # pylint: disable=import-outside-toplevel

    return __import__("pathlib").Path(manage.__file__).resolve().parent.parent


def test_resolve_prints_one_json_object_on_stdout(tmp_path):
    config_dir = _config(tmp_path, _bundle(tmp_path / "kb"))

    done = _run(_repo_root(), "resolve", cwd=tmp_path, config_dir=config_dir)

    payload = json.loads(done.stdout)
    assert done.returncode == 0
    assert payload["operation"] == "resolve"
    assert [b["id"] for b in payload["bundles"]] == ["personal"]
    assert "operations" in payload["catalog"]


def test_resolve_with_no_configuration_reports_no_catalog(tmp_path):
    done = _run(_repo_root(), "resolve", cwd=tmp_path, config_dir=tmp_path / "none")

    payload = json.loads(done.stdout)
    assert done.returncode == 0
    assert payload["catalog"] is None
    assert payload["bundles"] == []


def test_read_returns_document_content(tmp_path):
    root = _bundle(tmp_path / "kb")
    (root / "ops.md").write_text("# Ops\n", encoding="utf-8")
    config_dir = _config(tmp_path, root)

    done = _run(
        _repo_root(),
        "read",
        "--bundle",
        "personal",
        "--target",
        "ops.md",
        cwd=tmp_path,
        config_dir=config_dir,
    )

    payload = json.loads(done.stdout)
    assert done.returncode == 0
    assert payload["content"] == "# Ops\n"


def test_a_refused_read_exits_nonzero_with_a_stable_error_code(tmp_path):
    config_dir = _config(tmp_path, _bundle(tmp_path / "kb"))

    done = _run(
        _repo_root(),
        "read",
        "--bundle",
        "personal",
        "--target",
        "../secret.md",
        cwd=tmp_path,
        config_dir=config_dir,
    )

    payload = json.loads(done.stdout)
    assert done.returncode == 1
    assert payload["error"] == "path_escape"


def test_status_reports_declarations_and_paths(tmp_path):
    config_dir = _config(tmp_path, _bundle(tmp_path / "kb"))

    done = _run(_repo_root(), "status", cwd=tmp_path, config_dir=config_dir)

    payload = json.loads(done.stdout)
    assert done.returncode == 0
    assert payload["bundles"][0] == {
        "id": "personal",
        "active": True,
        "reason": "always",
        "path": str(config_dir / "personal"),
    }


def test_a_broken_configuration_still_exits_zero_with_diagnostics(tmp_path):
    """A hook must not fail the harness because a config file is malformed."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "config.yaml").write_text("version: 7\n", encoding="utf-8")

    done = _run(_repo_root(), "resolve", cwd=tmp_path, config_dir=config_dir)

    payload = json.loads(done.stdout)
    assert done.returncode == 0
    assert payload["catalog"] is None
    assert any(d["code"] == "config_error" for d in payload["diagnostics"])


def test_the_config_directory_can_be_passed_as_a_flag(tmp_path):
    config_dir = _config(tmp_path, _bundle(tmp_path / "kb"))

    done = _run(_repo_root(), "resolve", "--config-dir", str(config_dir), cwd=tmp_path)

    assert [b["id"] for b in json.loads(done.stdout)["bundles"]] == ["personal"]


def test_an_unknown_operation_fails_without_printing_json(tmp_path):
    done = _run(_repo_root(), "frobnicate", cwd=tmp_path)

    assert done.returncode == 2
    assert done.stdout == ""


def test_the_stowed_launcher_only_delegates():
    """`agents/bin/agent-knowledge` is extensionless, so it matches neither the
    *.py nor the *.sh lint glob. Keep it trivial: behaviour belongs in
    manage/knowledge/cli.py, which is linted and tested."""
    launcher = (_repo_root() / CLI).read_text(encoding="utf-8")
    body = ast.parse(launcher).body
    statements = [node for node in body if not isinstance(node, ast.Expr)]

    assert "from manage.knowledge.cli import main" in launcher
    assert len(statements) <= 6, "launcher grew logic that lint would not see"


def test_the_launcher_is_executable():
    assert os.access(_repo_root() / CLI, os.X_OK)


def test_a_hostile_source_cannot_read_outside_the_bundle(tmp_path):
    """The CLI is the Claude Code read path, reached through Bash, so the
    containment check has to hold at this boundary too."""
    root = _bundle(tmp_path / "kb")
    (tmp_path / "secret.md").write_text("secret\n", encoding="utf-8")
    config_dir = _config(tmp_path, root)

    done = _run(
        _repo_root(),
        "read",
        "--bundle",
        "personal",
        "--target",
        "secret.md",
        "--source",
        str(tmp_path / "index.md"),
        cwd=tmp_path,
        config_dir=config_dir,
    )

    payload = json.loads(done.stdout)
    assert done.returncode == 1
    assert payload["content"] is None
    assert payload["error"] in {"path_escape", "invalid_path"}


def test_no_project_withholds_the_discovered_bundle(tmp_path):
    """pi passes this through when its own trust decision says the repository's
    content should not be read yet."""
    project = tmp_path / "projects" / "repo"
    _bundle(project / "agents-knowledge")
    config_dir = _config(tmp_path, _bundle(tmp_path / "kb"))

    with_project = _run(_repo_root(), "resolve", cwd=project, config_dir=config_dir)
    without = _run(
        _repo_root(), "resolve", "--no-project", cwd=project, config_dir=config_dir
    )

    assert [b["id"] for b in json.loads(with_project.stdout)["bundles"]] == [
        "personal",
        "project",
    ]
    assert [b["id"] for b in json.loads(without.stdout)["bundles"]] == ["personal"]


def _clean_bundle(root):
    """The shared fixture's index links a concept it does not write, which is
    enough to resolve but not to pass a structure check."""
    _bundle(root)
    (root / "ops.md").write_text(
        "---\ntype: Reference\ntitle: Ops\ndescription: operations\n---\n# Ops\n",
        encoding="utf-8",
    )
    return root


def test_check_reports_no_problems_for_a_clean_bundle(tmp_path):
    config_dir = _config(tmp_path, _clean_bundle(tmp_path / "kb"))

    result = _run(_repo_root(), "check", config_dir=config_dir, cwd=tmp_path)

    assert result.returncode == 0
    assert json.loads(result.stdout)["problems"] == []


def test_check_exits_non_zero_so_a_private_repo_can_gate_on_it(tmp_path):
    """A dotfiles_local checkout has no CI of ours; the exit code is what lets
    it run this without parsing JSON."""
    root = tmp_path / "kb"
    _bundle(root)
    (root / "ops.md").write_text("no frontmatter, no heading\n", encoding="utf-8")

    result = _run(
        _repo_root(), "check", "--path", str(root), config_dir=tmp_path / "none"
    )

    assert result.returncode == 1
    assert json.loads(result.stdout)["problems"]


def test_check_without_a_path_checks_the_bundles_active_here(tmp_path):
    """Reported as the bundle was discovered -- the config-dir entry, not the
    directory it links to, so the id in `status` and the path here agree."""
    config_dir = _config(tmp_path, _clean_bundle(tmp_path / "kb"))

    result = _run(_repo_root(), "check", config_dir=config_dir, cwd=tmp_path)

    assert json.loads(result.stdout)["checked"] == [str(config_dir / "personal")]
