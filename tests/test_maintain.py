"""Tests for the maintenance run: pulling repos, picking groups, updating CLIs.

Pull is tested against real git repositories built in tmp_path, because the
behaviour that matters (a dirty tree, a diverged history) is git's own
refusal logic, which a mock would only restate.
"""

# Test names document each case, and these helpers are private to the module.
# Tests take the `remote` fixture as a parameter, which shadows its definition.
# pylint: disable=missing-function-docstring,redefined-outer-name

import pathlib
import subprocess

import pytest

from manage import maintain


def _git(cwd, *args):
    subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false", *args],
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
    )


def _commit(repo, name, text):
    (repo / name).write_text(text)
    _git(repo, "add", name)
    _git(repo, "commit", "-m", f"edit {name}")


@pytest.fixture
def remote(tmp_path):
    """An origin with one commit, a `clone` of it, and a `seed` clone to push from."""
    origin = tmp_path / "origin.git"
    _git(tmp_path, "init", "--bare", "-b", "main", str(origin))
    seed = tmp_path / "seed"
    _git(tmp_path, "clone", str(origin), str(seed))
    _commit(seed, "a.txt", "one\n")
    _commit(seed, "b.txt", "one\n")
    _git(seed, "push", "origin", "HEAD:main")
    clone = tmp_path / "clone"
    _git(tmp_path, "clone", str(origin), str(clone))
    return seed, clone


# --- pull --------------------------------------------------------------------


def test_pull_reports_current_when_nothing_is_new(remote):
    _, clone = remote
    assert maintain.pull(clone).status == "current"


def test_pull_reports_updated_when_origin_moved(remote):
    seed, clone = remote
    _commit(seed, "a.txt", "two\n")
    _git(seed, "push", "origin", "HEAD:main")

    assert maintain.pull(clone).status == "updated"
    assert (clone / "a.txt").read_text() == "two\n"


def test_pull_updates_a_dirty_tree_when_the_edits_do_not_overlap(remote):
    seed, clone = remote
    (clone / "a.txt").write_text("local edit\n")
    _commit(seed, "b.txt", "two\n")
    _git(seed, "push", "origin", "HEAD:main")

    assert maintain.pull(clone).status == "updated"
    assert (clone / "a.txt").read_text() == "local edit\n"
    assert (clone / "b.txt").read_text() == "two\n"


def test_pull_skips_when_a_local_edit_overlaps_the_incoming_change(remote):
    seed, clone = remote
    (clone / "a.txt").write_text("local edit\n")
    _commit(seed, "a.txt", "two\n")
    _git(seed, "push", "origin", "HEAD:main")

    result = maintain.pull(clone)

    assert result.status == "skipped"
    assert result.detail
    assert (clone / "a.txt").read_text() == "local edit\n"


def test_pull_skips_a_diverged_history(remote):
    seed, clone = remote
    _commit(clone, "a.txt", "local commit\n")
    _commit(seed, "b.txt", "two\n")
    _git(seed, "push", "origin", "HEAD:main")

    result = maintain.pull(clone)

    assert result.status == "skipped"
    assert (clone / "a.txt").read_text() == "local commit\n"


def test_pull_reports_missing_for_a_path_that_is_not_a_repo(tmp_path):
    assert maintain.pull(tmp_path / "nowhere").status == "missing"


# --- group selection ---------------------------------------------------------


def test_every_group_runs_in_order_by_default():
    assert maintain.select_groups() == ["pull", "cli", "plugins", "stow", "local"]


def test_only_keeps_the_named_groups_in_run_order():
    assert maintain.select_groups(only="stow,pull") == ["pull", "stow"]


def test_skip_removes_the_named_groups():
    assert maintain.select_groups(skip="cli, local") == ["pull", "plugins", "stow"]


def test_an_unknown_group_name_is_an_error():
    with pytest.raises(ValueError, match="bogus"):
        maintain.select_groups(only="pull,bogus")


# --- cli updates -------------------------------------------------------------


def test_claude_is_upgraded_with_npm_into_the_user_prefix():
    home = pathlib.Path("/home/u")
    cmds = maintain.cli_commands({"npm_global_packages": ["@anthropic-ai/claude-code"]}, home)

    npm = cmds[0]
    assert npm.argv == ["npm", "install", "-g", "@anthropic-ai/claude-code@latest"]
    assert npm.env["NPM_CONFIG_PREFIX"] == "/home/u/.local"


def test_pi_is_upgraded_with_its_own_updater_and_a_pnpm_home():
    home = pathlib.Path("/home/u")
    cmds = maintain.cli_commands({"npm_global_packages": []}, home)

    pi = cmds[-1]
    assert pi.argv == ["pi", "update", "--self"]
    assert pi.env["PNPM_HOME"] == "/home/u/.local/share/pnpm"
    assert "/home/u/.local/share/pnpm" in pi.env["PATH"].split(":")


# --- worktree guard ----------------------------------------------------------


def test_a_linked_worktree_is_detected_and_the_main_checkout_is_not(remote, tmp_path):
    _, clone = remote
    linked = tmp_path / "linked"
    _git(clone, "worktree", "add", "-b", "other", str(linked))

    assert maintain.is_linked_worktree(linked)
    assert not maintain.is_linked_worktree(clone)
