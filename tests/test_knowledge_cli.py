"""Tests for the CLI every harness adapter shells out to.

The adapters are the reason this is a process boundary: a Pi extension, a Claude
hook and an OpenCode plugin cannot import Python, so JSON on stdout is the one
contract all three share.
"""

# Test names document each case, and the helpers are private to the module.
# pylint: disable=missing-function-docstring

import json
import os
import subprocess
import sys

CLI = "scripts/bin/agent-knowledge"

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
    root = _bundle(tmp_path / "kb")
    config_dir = _config(tmp_path, root)

    done = _run(_repo_root(), "status", cwd=tmp_path, config_dir=config_dir)

    payload = json.loads(done.stdout)
    assert done.returncode == 0
    assert payload["bundles"][0] == {
        "id": "personal",
        "active": True,
        "reason": "always",
        "path": str(root),
    }


def test_a_broken_configuration_still_exits_zero_with_diagnostics(tmp_path):
    """A hook must not fail the harness because a config file is malformed."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "bundles.yaml").write_text("version: 7\n", encoding="utf-8")

    done = _run(_repo_root(), "resolve", cwd=tmp_path, config_dir=config_dir)

    payload = json.loads(done.stdout)
    assert done.returncode == 0
    assert payload["catalog"] is None
    assert any(d["code"] == "config_error" for d in payload["diagnostics"])


def test_the_config_directory_can_be_passed_as_a_flag(tmp_path):
    config_dir = _config(tmp_path, _bundle(tmp_path / "kb"))

    done = _run(
        _repo_root(), "resolve", "--config-dir", str(config_dir), cwd=tmp_path
    )

    assert [b["id"] for b in json.loads(done.stdout)["bundles"]] == ["personal"]


def test_an_unknown_operation_fails_without_printing_json(tmp_path):
    done = _run(_repo_root(), "frobnicate", cwd=tmp_path)

    assert done.returncode == 2
    assert done.stdout == ""
