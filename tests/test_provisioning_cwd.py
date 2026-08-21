"""Tests that provisioning does not move the process's working directory.

Invoke runs pre-tasks in one process, so a directory change that outlives its
command leaks into whatever runs next -- `inv all` runs provision and then stow,
and stow resolves its package paths relative to the repo root.
"""

# Test names document each case, and these helpers are private to the module.
# pylint: disable=missing-function-docstring,protected-access

import contextlib
import os
import pathlib

import tasks


class _FakeContext:
    """Records what was run and where, without running anything."""

    def __init__(self):
        self.commands = []
        self.directories = []

    @contextlib.contextmanager
    def cd(self, path):
        self.directories.append(str(path))
        yield

    def run(self, command, **_kwargs):
        self.commands.append(command)


def test_provisioning_leaves_the_working_directory_alone():
    ctx = _FakeContext()
    before = os.getcwd()

    tasks._provision_linux(ctx, is_ci=True, args="")

    assert os.getcwd() == before


def test_the_playbook_runs_from_the_ansible_directory():
    ctx = _FakeContext()

    tasks._provision_linux(ctx, is_ci=True, args="")

    assert ctx.directories == [tasks.ANSIBLE_DIR]
    assert "site.yml" in ctx.commands[0]


def test_provision_all_leaves_the_working_directory_alone():
    ctx = _FakeContext()
    before = os.getcwd()

    # .body bypasses invoke's Context type check on the task wrapper.
    tasks.provision_all.body(ctx)

    assert os.getcwd() == before
    assert ctx.directories == [tasks.ANSIBLE_DIR]


def test_stow_packages_still_resolve_after_provisioning():
    """The failure this guards: relative package paths resolving from ansible/.

    Dploy.clean caps its traversal depth by globbing every stow package by its
    bare relative name. From anywhere but the repo root those match nothing, and
    the max() over an empty sequence raises before any sweeping happens.
    """
    ctx = _FakeContext()

    tasks._provision_linux(ctx, is_ci=True, args="")

    assert list(pathlib.Path("agents").rglob("*")), "agents/ no longer resolves"
