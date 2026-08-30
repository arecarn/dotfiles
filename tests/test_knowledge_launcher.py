"""Tests pinning where the CLI is installed, since three adapters hardcode it.

Each adapter invokes the launcher by absolute path -- a harness hook does not
inherit a shell that has set PATH. That makes the stow destination part of the
contract rather than an implementation detail, so it is asserted here on the
repo's own layout instead of being rediscovered per adapter.
"""

# Test names document each case, and the helpers are private to the module.
# pylint: disable=missing-function-docstring

import pathlib
import re
import subprocess
import sys

LAUNCHER = "agents/bin/agent-knowledge"

# agents/bin/<file> stows to ~/bin/<file>; see manage.stow._STOW_PACKAGES.
INSTALLED = "~/bin/agent-knowledge"

ADAPTERS = (
    "pi/.pi/agent/extensions/agent-knowledge/resolver.ts",
    "opencode/.config/opencode/plugins/agent-knowledge.ts",
)


def _repo_root():
    return pathlib.Path(__file__).resolve().parent.parent


def test_the_launcher_is_in_the_scripts_package():
    assert (_repo_root() / LAUNCHER).is_file()


def test_every_adapter_points_at_the_installed_path():
    """A wrong path here fails silently: the adapter treats a missing CLI as
    "no knowledge configured" so it cannot break a session."""
    for adapter in ADAPTERS:
        text = (_repo_root() / adapter).read_text(encoding="utf-8")
        joined = re.search(
            r'join\(process\.env\.HOME \|\| homedir\(\),([^)]*)\)', text
        )
        assert joined, f"{adapter} does not build the CLI path from HOME/homedir()"
        segments = re.findall(r'"([^"]+)"', joined.group(1))
        assert segments == ["bin", "agent-knowledge"], (
            f"{adapter} looks for the CLI at ~/{'/'.join(segments)}, "
            f"but stow installs it at {INSTALLED}"
        )


def test_the_launcher_runs_without_this_repo_dev_dependencies():
    """A harness hook runs the launcher under whatever `python3` it finds, not
    this repo's venv. Importing `manage` would drag in ruamel.yaml through
    manage.agents, so the CLI must reach manage.knowledge without it."""
    root = _repo_root()
    probe = (
        "import sys, pathlib;"
        "sys.modules['ruamel'] = None;"
        f"sys.path.insert(0, {str(root)!r});"
        "import manage.knowledge.cli"
    )

    done = subprocess.run(
        [sys.executable, "-c", probe],
        capture_output=True,
        text=True,
        check=False,
        cwd=str(root),
    )

    assert done.returncode == 0, done.stderr
