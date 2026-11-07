"""Contract tests for the watch-ci skill's watcher script.

The script is exercised against stub `gh` and `glab` commands in a scratch git
repo, so what is checked is how it selects a run and what it reports, not a
real provider's behaviour.
"""

# Test names document each case, and the helpers are private to the module.
# pylint: disable=missing-function-docstring

import os
import pathlib
import shutil
import subprocess
import sys

import pytest

SCRIPT = pathlib.Path("agents/.config/ai-skills/skills/watch-ci/watch.sh").resolve()

BASH = shutil.which("bash")
needs_bash = pytest.mark.skipif(
    BASH is None
    or subprocess.run([BASH, "-c", "true"], capture_output=True, check=False).returncode
    != 0,
    reason="a working bash is not installed",
)
# The stubs are bash scripts found through PATH, which Windows resolves
# differently; the syntax and content checks above still run there.
posix_only = pytest.mark.skipif(sys.platform == "win32", reason="PATH stubs need POSIX")


def _git(cwd, *args):
    return subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@t", *args],
        cwd=cwd, capture_output=True, text=True, check=True,
    ).stdout.strip()


def _repo(tmp_path, *, workflows=(), gitlab=False):
    _git(tmp_path, "init", "-q", ".")
    _git(tmp_path, "commit", "-q", "--allow-empty", "-m", "x")
    if workflows:
        (tmp_path / ".github" / "workflows").mkdir(parents=True)
        for name in workflows:
            (tmp_path / ".github" / "workflows" / name).write_text("")
    if gitlab:
        (tmp_path / ".gitlab-ci.yml").write_text("")
    return tmp_path


def _stub(tmp_path, name, body):
    """Install a stub `name` command; it logs its arguments to calls.log."""
    bin_dir = tmp_path / "stub-bin"
    bin_dir.mkdir(exist_ok=True)
    path = bin_dir / name
    path.write_text(f'#!/bin/sh\necho "$*" >> "{tmp_path}/calls.log"\n{body}\n')
    path.chmod(0o755)
    return bin_dir


def _run(repo, *args, stubs=None):
    env = {**os.environ}
    if stubs:
        env["PATH"] = f"{stubs}{os.pathsep}{env['PATH']}"
    return subprocess.run(
        [BASH, str(SCRIPT), *args],
        cwd=repo, env=env, capture_output=True, text=True, check=False, timeout=60,
    )


def test_the_script_is_valid_shell():
    if BASH is None:
        pytest.skip("a working bash is not installed")

    done = subprocess.run([BASH, "-n", str(SCRIPT)], capture_output=True, text=True, check=False)

    assert done.returncode == 0, done.stderr


@needs_bash
def test_no_ci_config_is_a_startup_error_not_a_result(tmp_path):
    done = _run(_repo(tmp_path))

    assert done.returncode == 2
    assert "nothing to watch" in done.stderr


@needs_bash
def test_both_providers_present_demands_a_choice(tmp_path):
    done = _run(_repo(tmp_path, workflows=["ci.yml"], gitlab=True))

    assert done.returncode == 2
    assert "--provider" in done.stderr


@needs_bash
def test_several_workflows_without_a_choice_lists_them(tmp_path):
    done = _run(_repo(tmp_path, workflows=["a.yml", "b.yml"]))

    assert done.returncode == 2
    assert "a.yml" in done.stderr and "b.yml" in done.stderr


GH_STUB = """\
case "$*" in
  "run list"*) echo 123 ;;
  "run view 123 --json conclusion --jq"*) echo success ;;
  "run view 123 --json conclusion,url"*) echo "success https://x/123 workflow=CI" ;;
esac
"""


@needs_bash
@posix_only
def test_github_selects_by_full_sha_and_workflow_and_reports_the_result(tmp_path):
    repo = _repo(tmp_path, workflows=["ci.yml"])
    stubs = _stub(tmp_path, "gh", GH_STUB)
    full = _git(repo, "rev-parse", "HEAD")

    done = _run(repo, stubs=stubs)

    assert done.returncode == 0, done.stderr
    assert done.stdout.startswith("success https://x/123")
    listing = next(
        line for line in (tmp_path / "calls.log").read_text().splitlines()
        if line.startswith("run list")
    )
    assert f"--commit {full}" in listing
    assert "--workflow ci.yml" in listing


@needs_bash
@posix_only
def test_an_abbreviated_sha_is_resolved_to_the_full_one(tmp_path):
    repo = _repo(tmp_path, workflows=["ci.yml"])
    stubs = _stub(tmp_path, "gh", GH_STUB)
    full = _git(repo, "rev-parse", "HEAD")

    _run(repo, "--sha", full[:7], stubs=stubs)

    assert f"--commit {full}" in (tmp_path / "calls.log").read_text()


@needs_bash
@posix_only
def test_a_failed_run_is_reported_with_exit_zero(tmp_path):
    repo = _repo(tmp_path, workflows=["ci.yml"])
    stubs = _stub(tmp_path, "gh", GH_STUB.replace("echo success", "echo failure").replace(
        '"success https', '"failure https'))

    done = _run(repo, stubs=stubs)

    assert done.returncode == 0
    assert done.stdout.startswith("failure")


GL_STUB = """\
case "$*" in
  *"pipelines?sha="*) echo 77 ;;
  *"web_url"*) echo "success https://gl/77 sha=abc source=push" ;;
  *".status"*) echo success ;;
esac
"""


@needs_bash
@posix_only
def test_gitlab_selects_by_full_sha_and_reports_the_result(tmp_path):
    repo = _repo(tmp_path, gitlab=True)
    stubs = _stub(tmp_path, "glab", GL_STUB)
    full = _git(repo, "rev-parse", "HEAD")

    done = _run(repo, stubs=stubs)

    assert done.returncode == 0, done.stderr
    assert done.stdout.startswith("success https://gl/77")
    assert f"pipelines?sha={full}" in (tmp_path / "calls.log").read_text()
