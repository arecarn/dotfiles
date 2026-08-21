"""Tests for the missing-linter policy in tasks.py.

A linter whose binary is absent is a hard error under CI and a loud, recorded
skip locally. These tests pin both halves, plus the platform scoping that keeps
shell linting off Windows entirely.
"""

# Test names document each case, and these helpers are private to the module.
# pylint: disable=missing-function-docstring,protected-access,too-few-public-methods

import pytest

import tasks


class _FakeContext:
    """Records what was run, without running anything."""

    def __init__(self):
        self.commands = []

    def run(self, command, **_kwargs):
        self.commands.append(command)


@pytest.fixture(name="ctx")
def _ctx():
    return _FakeContext()


@pytest.fixture(autouse=True)
def _clear_skips():
    tasks.SKIPPED_LINTERS.clear()
    yield
    tasks.SKIPPED_LINTERS.clear()


def _tool_is(monkeypatch, present: bool):
    monkeypatch.setattr(
        tasks.shutil, "which", lambda _tool: "/usr/bin/tool" if present else None
    )


def test_present_tool_runs(ctx, monkeypatch):
    _tool_is(monkeypatch, True)
    monkeypatch.setattr(tasks, "IS_CI", False)

    tasks._run_linter(ctx, "stylua", "stylua --check a.lua")

    assert ctx.commands == ["stylua --check a.lua"]
    assert not tasks.SKIPPED_LINTERS


def test_missing_tool_is_skipped_and_recorded_locally(ctx, monkeypatch):
    _tool_is(monkeypatch, False)
    monkeypatch.setattr(tasks, "IS_CI", False)

    tasks._run_linter(ctx, "stylua", "stylua --check a.lua")

    assert ctx.commands == []
    assert tasks.SKIPPED_LINTERS == ["stylua"]


def test_missing_tool_fails_in_ci(ctx, monkeypatch):
    _tool_is(monkeypatch, False)
    monkeypatch.setattr(tasks, "IS_CI", True)

    with pytest.raises(SystemExit, match="stylua"):
        tasks._run_linter(ctx, "stylua", "stylua --check a.lua")

    assert ctx.commands == []


def test_lint_reports_the_skipped_linters(ctx, monkeypatch, capsys):
    _tool_is(monkeypatch, False)
    monkeypatch.setattr(tasks, "IS_CI", False)
    tasks._run_linter(ctx, "stylua", "stylua --check a.lua")

    tasks.lint.body(ctx)

    assert "stylua" in capsys.readouterr().out


def test_lint_says_nothing_when_every_linter_ran(ctx, capsys):
    tasks.lint.body(ctx)

    assert capsys.readouterr().out == ""


def test_shell_lint_is_scoped_out_of_windows(ctx, monkeypatch):
    monkeypatch.setattr(tasks, "IS_WINDOWS", True)
    # Windows must not reach the policy at all: a shellcheck that is absent
    # by design is not an install failure.
    monkeypatch.setattr(tasks, "IS_CI", True)
    _tool_is(monkeypatch, False)

    tasks.lint_shell.body(ctx)

    assert ctx.commands == []
    assert not tasks.SKIPPED_LINTERS


def test_shell_lint_runs_shellcheck_elsewhere(ctx, monkeypatch):
    monkeypatch.setattr(tasks, "IS_WINDOWS", False)
    monkeypatch.setattr(tasks, "IS_CI", False)
    _tool_is(monkeypatch, True)

    tasks.lint_shell.body(ctx)

    assert len(ctx.commands) == 1
    assert ctx.commands[0].startswith("shellcheck --format gcc ")
