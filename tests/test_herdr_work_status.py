"""Tests for the Claude Code herdr work-status hook.

The module under test lives at a path that is not importable (dotted and
dashed segments), so it is loaded from its file. Its helpers are its only
caller.
"""

# pylint: disable=missing-function-docstring,protected-access

import importlib.util
import os
import pathlib
import subprocess
import sys

import pytest

_HOOK = (
    pathlib.Path(__file__).resolve().parents[1]
    / "claude-code/.claude/hooks/herdr_work_status.py"
)

_posix_only = pytest.mark.skipif(
    sys.platform == "win32",
    reason="POSIX only: flock + /bin/sh fake herdr",
)


def _load():
    spec = importlib.util.spec_from_file_location("herdr_work_status", _HOOK)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


hws = _load()


def test_format_token_none_when_no_agents():
    assert hws.format_token(0) is None
    assert hws.format_token(-1) is None


def test_format_token_counts_running_agents():
    assert hws.format_token(1) == "A1"
    assert hws.format_token(3) == "A3"


def test_subagent_start_adds_the_id():
    state = hws.next_state({"agents": []}, {
        "hook_event_name": "SubagentStart", "agent_id": "a1"})
    assert state == {"agents": ["a1"]}


def test_subagent_start_is_idempotent_per_id():
    state = {"agents": ["a1"]}
    state = hws.next_state(state, {
        "hook_event_name": "SubagentStart", "agent_id": "a1"})
    assert state == {"agents": ["a1"]}


def test_two_agents_then_one_stop():
    state = {"agents": []}
    for agent_id in ("a1", "a2"):
        state = hws.next_state(state, {
            "hook_event_name": "SubagentStart", "agent_id": agent_id})
    state = hws.next_state(state, {
        "hook_event_name": "SubagentStop", "agent_id": "a1"})
    assert state == {"agents": ["a2"]}


def test_subagent_stop_for_unknown_id_is_a_noop():
    state = hws.next_state({"agents": ["a1"]}, {
        "hook_event_name": "SubagentStop", "agent_id": "ghost"})
    assert state == {"agents": ["a1"]}


def test_subagent_stop_when_empty_stays_empty():
    state = hws.next_state({"agents": []}, {
        "hook_event_name": "SubagentStop", "agent_id": "a1"})
    assert state == {"agents": []}


def test_session_events_reset_the_list():
    for name in ("SessionStart", "SessionEnd"):
        state = hws.next_state({"agents": ["a1", "a2"]}, {
            "hook_event_name": name})
        assert state == {"agents": []}


def test_unknown_or_malformed_event_leaves_state_unchanged():
    assert hws.next_state({"agents": ["a1"]}, {}) == {"agents": ["a1"]}
    assert hws.next_state({"agents": ["a1"]}, {"hook_event_name": "Stop"}) == {
        "agents": ["a1"]}
    assert hws.next_state({"agents": ["a1"]}, "not-a-dict") == {"agents": ["a1"]}


def _fake_herdr(tmp_path):
    """A stand-in `herdr` binary that appends its arguments to calls.log."""
    log = tmp_path / "calls.log"
    binary = tmp_path / "herdr"
    binary.write_text(f'#!/bin/sh\nprintf "%s\\n" "$*" >> "{log}"\n')
    binary.chmod(0o755)
    return binary, log


def _run_hook(tmp_path, payload, *, herdr_env):
    binary, log = _fake_herdr(tmp_path)
    env = {
        **os.environ,
        "HERDR_PANE_ID": "wX:p1",
        "HERDR_BIN_PATH": str(binary),
        "XDG_RUNTIME_DIR": str(tmp_path),
    }
    if herdr_env:
        env["HERDR_ENV"] = "1"
    else:
        env.pop("HERDR_ENV", None)
    done = subprocess.run(
        [sys.executable, str(_HOOK)],
        input=payload, text=True, env=env, capture_output=True, check=False,
    )
    return done, log


@_posix_only
def test_main_publishes_a1_on_subagent_start_inside_herdr(tmp_path):
    done, log = _run_hook(
        tmp_path,
        '{"hook_event_name":"SubagentStart","session_id":"s1","agent_id":"a1"}',
        herdr_env=True,
    )
    assert done.returncode == 0
    assert "work_status=A1" in log.read_text()
    assert (tmp_path / "herdr-claude-work" / "s1.json").exists()


@_posix_only
def test_main_is_inert_without_herdr_env(tmp_path):
    done, log = _run_hook(
        tmp_path,
        '{"hook_event_name":"SubagentStart","session_id":"s1","agent_id":"a1"}',
        herdr_env=False,
    )
    assert done.returncode == 0
    assert not log.exists()
    assert not (tmp_path / "herdr-claude-work").exists()


@_posix_only
def test_main_clears_the_token_and_state_on_session_end(tmp_path):
    _run_hook(
        tmp_path,
        '{"hook_event_name":"SubagentStart","session_id":"s2","agent_id":"a1"}',
        herdr_env=True,
    )
    done, log = _run_hook(
        tmp_path,
        '{"hook_event_name":"SessionEnd","session_id":"s2"}',
        herdr_env=True,
    )
    assert done.returncode == 0
    assert "--clear-token work_status" in log.read_text()
    assert not (tmp_path / "herdr-claude-work" / "s2.json").exists()


@_posix_only
def test_main_is_inert_when_pane_id_is_unset(tmp_path):
    binary, log = _fake_herdr(tmp_path)
    env = {
        **os.environ,
        "HERDR_ENV": "1",
        "HERDR_BIN_PATH": str(binary),
        "XDG_RUNTIME_DIR": str(tmp_path),
    }
    env.pop("HERDR_PANE_ID", None)
    done = subprocess.run(
        [sys.executable, str(_HOOK)],
        input='{"hook_event_name":"SubagentStart","session_id":"s1","agent_id":"a1"}',
        text=True, env=env, capture_output=True, check=False,
    )
    assert done.returncode == 0
    assert not log.exists()
    assert not (tmp_path / "herdr-claude-work").exists()


def test_main_is_inert_without_a_session_id(tmp_path):
    # main() returns 0 after the `if not session_id` guard, before any I/O; the
    # subprocess path confirms nothing is written or published.
    binary, log = _fake_herdr(tmp_path)
    env = {
        **os.environ,
        "HERDR_ENV": "1",
        "HERDR_PANE_ID": "wX:p1",
        "HERDR_BIN_PATH": str(binary),
        "XDG_RUNTIME_DIR": str(tmp_path),
    }
    done = subprocess.run(
        [sys.executable, str(_HOOK)],
        input='{"hook_event_name":"SubagentStart","agent_id":"a1"}',
        text=True, env=env, capture_output=True, check=False,
    )
    assert done.returncode == 0
    assert not log.exists()
    assert not (tmp_path / "herdr-claude-work").exists()
