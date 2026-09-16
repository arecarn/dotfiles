"""Shared on/off state for the obra/superpowers bootstrap prompt.

Superpowers injects an `<EXTREMELY_IMPORTANT>` "You have superpowers" block once
per session (again after a pi compaction, or a fresh Claude Code session) with no
built-in way to turn it off short of uninstalling the plugin -- which also drops
its skills. This module is the one flag both harnesses' adapters read, so a
single `superpowers-toggle off` suppresses the *next* injection in either. It
cannot retract a block already sent to the model this session: pi's context
injection is not stored in session state, and Claude's SessionStart hook already
fired. See docs/adr/ for the decision this implements.

State lives under `~/.local/state`, not `~/.config`, because it is runtime
toggle state a human flips, not declared configuration a machine provisions --
the same distinction XDG draws between the two directories.
"""

import os
import pathlib

# Overridable for tests, matching manage.knowledge.cli's CONFIG_DIR_ENV pattern.
STATE_DIR_ENV = "SUPERPOWERS_TOGGLE_STATE_DIR"

_ON = "on"
_OFF = "off"
_STATE_FILE = "superpowers-bootstrap"


def state_dir(explicit=None):
    """The state directory: an explicit path, then the env var, then the XDG default."""
    if explicit:
        return pathlib.Path(explicit)
    from_env = os.environ.get(STATE_DIR_ENV)
    if from_env:
        return pathlib.Path(from_env)
    xdg = os.environ.get("XDG_STATE_HOME") or (pathlib.Path.home() / ".local" / "state")
    return pathlib.Path(xdg) / "ai-skills"


def _flag_path(directory):
    return directory / _STATE_FILE


def is_enabled(directory=None):
    """Whether the bootstrap should inject: true unless the flag file says "off".

    Absent file means enabled -- a machine that never ran the toggle behaves
    exactly as superpowers ships, which is what a fresh install must do.
    """
    path = _flag_path(state_dir(directory))
    if not path.exists():
        return True
    return path.read_text(encoding="utf-8").strip() != _OFF


def set_enabled(enabled, directory=None):
    """Persist on/off. Deletes the file for "on" so an untouched install stays fileless."""
    path = _flag_path(state_dir(directory))
    if enabled:
        path.unlink(missing_ok=True)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_OFF, encoding="utf-8")
