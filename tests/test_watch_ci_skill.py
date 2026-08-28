"""Contract tests for the watch-ci skill's copy-paste GitHub watcher."""

# Test names document each case, and the helper is private to the module.
# pylint: disable=missing-function-docstring

import pathlib
import re
import shutil
import subprocess

import pytest

SKILL = pathlib.Path("agents/.config/ai-skills/skills/watch-ci/SKILL.md")


def _github_script():
    text = SKILL.read_text(encoding="utf-8")
    section = text.split("## GitHub Actions", 1)[1].split("## GitLab CI", 1)[0]
    match = re.search(r"```bash\n(.*?)\n```", section, re.DOTALL)
    assert match is not None
    return match.group(1)


def test_github_watcher_resolves_a_full_sha_before_querying_runs():
    script = _github_script()

    assert 'sha=$(git rev-parse HEAD)' in script
    assert 'gh run list --commit "$sha"' in script


def test_github_watcher_reports_job_conclusions_in_its_terminal_event():
    script = _github_script()

    assert "conclusion,url,workflowName,headSha,jobs" in script
    assert ".jobs[]" in script


def test_github_watcher_is_valid_shell():
    bash = shutil.which("bash")
    if bash is None or subprocess.run(
        [bash, "-c", "true"], capture_output=True, check=False
    ).returncode != 0:
        pytest.skip("a working bash is not installed")

    done = subprocess.run(
        [bash, "-n"],
        input=_github_script(),
        capture_output=True,
        text=True,
        check=False,
    )

    assert done.returncode == 0, done.stderr
