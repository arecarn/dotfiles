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

LAUNCHER = "scripts/bin/agent-knowledge"

# scripts/bin/<file> stows to ~/bin/<file>; see manage.stow._STOW_PACKAGES.
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
        joined = re.search(r'join\(homedir\(\),([^)]*)\)', text)
        assert joined, f"{adapter} does not build the CLI path from homedir()"
        segments = re.findall(r'"([^"]+)"', joined.group(1))
        assert segments == ["bin", "agent-knowledge"], (
            f"{adapter} looks for the CLI at ~/{'/'.join(segments)}, "
            f"but stow installs it at {INSTALLED}"
        )
