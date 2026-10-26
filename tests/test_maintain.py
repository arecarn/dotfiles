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
import types

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


# --- pull group --------------------------------------------------------------


@pytest.fixture
def home(tmp_path, remote):
    """A fake $HOME holding fresh clones named like the real checkouts."""
    _, _ = remote
    home_dir = tmp_path / "home"
    home_dir.mkdir()
    for name in ("dotfiles", "dotfiles_local"):
        _git(tmp_path, "clone", str(tmp_path / "origin.git"), str(home_dir / name))
    return home_dir


def _push_change(remote, name, text):
    seed, _ = remote
    _commit(seed, name, text)
    _git(seed, "push", "origin", "HEAD:main")


def test_pull_group_is_ok_and_names_each_repo(home):
    outcome = maintain.pull_group(home)

    assert outcome.status == "ok"
    assert "dotfiles: current" in outcome.detail
    assert "dotfiles_local: current" in outcome.detail


def test_a_skipped_dotfiles_pull_is_partial_and_blocks_dependents(home, remote):
    _push_change(remote, "a.txt", "two\n")
    (home / "dotfiles" / "a.txt").write_text("local edit\n")

    outcome = maintain.pull_group(home)

    assert outcome.status == "partial"
    assert outcome.blocks
    assert "dotfiles: skipped" in outcome.detail


def test_a_skipped_dotfiles_local_pull_is_partial_but_does_not_block(home, remote):
    _push_change(remote, "a.txt", "two\n")
    (home / "dotfiles_local" / "a.txt").write_text("local edit\n")

    outcome = maintain.pull_group(home)

    assert outcome.status == "partial"
    assert not outcome.blocks


def test_a_missing_dotfiles_checkout_blocks_dependents(tmp_path):
    outcome = maintain.pull_group(tmp_path)

    assert outcome.status == "partial"
    assert outcome.blocks
    assert "dotfiles: missing" in outcome.detail


# --- running groups ----------------------------------------------------------


def _runners(**by_name):
    return {name: by_name.get(name, lambda: None) for name in maintain.GROUPS}


def test_a_runner_returning_nothing_is_ok():
    results = maintain.run_groups(["cli"], _runners(), emit=lambda _: None)

    assert results["cli"] == maintain.Outcome("ok")


def test_a_runner_raising_is_failed_and_later_groups_still_run():
    ran = []

    def boom():
        raise RuntimeError("npm exploded")

    results = maintain.run_groups(
        ["cli", "plugins"],
        _runners(cli=boom, plugins=lambda: ran.append("plugins")),
        emit=lambda _: None,
    )

    assert results["cli"].status == "FAILED"
    assert "npm exploded" in results["cli"].detail
    assert ran == ["plugins"]


def test_stow_is_skipped_when_pull_blocks_it():
    ran = []
    blocked = maintain.Outcome("partial", "dotfiles: skipped", blocks=True)

    results = maintain.run_groups(
        ["pull", "stow"],
        _runners(pull=lambda: blocked, stow=lambda: ran.append("stow")),
        emit=lambda _: None,
    )

    assert results["stow"].status == "skipped"
    assert "dotfiles: skipped" in results["stow"].detail
    assert not ran


def test_stow_runs_when_pull_only_skipped_dotfiles_local():
    ran = []
    soft = maintain.Outcome("partial", "dotfiles_local: skipped")

    maintain.run_groups(
        ["pull", "stow"],
        _runners(pull=lambda: soft, stow=lambda: ran.append("stow")),
        emit=lambda _: None,
    )

    assert ran == ["stow"]


def test_stow_runs_alone_when_pull_was_not_selected():
    ran = []

    maintain.run_groups(["stow"], _runners(stow=lambda: ran.append("stow")), emit=lambda _: None)

    assert ran == ["stow"]


def test_a_failed_pull_also_blocks_stow():
    def boom():
        raise RuntimeError("git missing")

    results = maintain.run_groups(["pull", "stow"], _runners(pull=boom), emit=lambda _: None)

    assert results["stow"].status == "skipped"


def test_the_summary_lists_each_group_and_flags_a_changed_version():
    results = {
        "pull": maintain.Outcome("ok", "dotfiles: current"),
        "cli": maintain.Outcome("FAILED", "npm failed"),
    }

    text = maintain.format_summary(
        results, {"claude": "2.1.1", "pi": "1.0"}, {"claude": "2.1.2", "pi": "1.0"}
    )

    assert "pull" in text and "dotfiles: current" in text
    assert "FAILED" in text and "npm failed" in text
    assert "2.1.2" in text and "was 2.1.1" in text
    assert "was 1.0" not in text


def test_any_failed_group_means_a_failing_run():
    assert maintain.any_failed({"a": maintain.Outcome("ok"), "b": maintain.Outcome("FAILED", "x")})
    assert not maintain.any_failed({"a": maintain.Outcome("partial", "x")})


# --- cli updates -------------------------------------------------------------

_GROUP_VARS = {"npm_global_packages": ["@anthropic-ai/claude-code"], "npm_prefix_subpath": ".local"}
_HOME = pathlib.Path("/home/u")


def test_claude_is_upgraded_with_npm_into_the_prefix_ansible_declares():
    npm = maintain.cli_commands(_GROUP_VARS, _HOME)[0]

    assert npm.argv == ["npm", "install", "-g", "@anthropic-ai/claude-code@latest"]
    assert npm.env["NPM_CONFIG_PREFIX"] == "/home/u/.local"


def test_a_different_prefix_in_group_vars_is_followed():
    npm = maintain.cli_commands({**_GROUP_VARS, "npm_prefix_subpath": ".npm-global"}, _HOME)[0]

    assert npm.env["NPM_CONFIG_PREFIX"] == "/home/u/.npm-global"


def test_pi_is_upgraded_with_its_own_updater_and_a_pnpm_home_on_path():
    pi = maintain.cli_commands(_GROUP_VARS, _HOME)[-1]

    assert pi.argv == ["pi", "update", "--self"]
    assert pi.env["PNPM_HOME"] == "/home/u/.local/share/pnpm"
    assert pi.prepend_path == "/home/u/.local/share/pnpm"


def test_on_windows_the_users_own_npm_and_pnpm_setup_is_left_alone():
    commands = maintain.cli_commands(_GROUP_VARS, _HOME, windows=True)

    assert [c.argv[0] for c in commands] == ["npm", "pi"]
    assert all(not c.env and not c.prepend_path for c in commands)


_Done = types.SimpleNamespace  # stands in for subprocess.CompletedProcess


def _upgrade(commands, *, installed=("npm", "pi"), exit_codes=None):
    calls = []
    codes = exit_codes or {}

    def fake_run(argv, env, check):  # pylint: disable=unused-argument
        calls.append((argv, env))
        return _Done(returncode=codes.get(argv[0], 0))

    def fake_which(name, path=None):  # pylint: disable=unused-argument
        return f"/bin/{name}" if name in installed else None

    outcome = maintain.upgrade_clis(
        commands, {"PATH": "/usr/bin"}, run=fake_run, which=fake_which, emit=lambda _: None
    )
    return outcome, calls


def test_upgrading_runs_each_command_with_its_environment():
    commands = maintain.cli_commands(_GROUP_VARS, _HOME)

    outcome, calls = _upgrade(commands)

    assert outcome.status == "ok"
    assert calls[0][0] == ["/bin/npm", "install", "-g", "@anthropic-ai/claude-code@latest"]
    assert calls[0][1]["NPM_CONFIG_PREFIX"] == "/home/u/.local"
    assert calls[1][1]["PATH"].startswith("/home/u/.local/share/pnpm")


def test_a_tool_that_is_not_installed_is_skipped_with_a_note():
    commands = maintain.cli_commands(_GROUP_VARS, _HOME)

    outcome, calls = _upgrade(commands, installed=("npm",))

    assert outcome.status == "partial"
    assert "pi" in outcome.detail
    assert len(calls) == 1


def test_a_failing_upgrade_raises_after_trying_the_rest():
    commands = maintain.cli_commands(_GROUP_VARS, _HOME)
    calls = []

    def fake_run(argv, env, check):  # pylint: disable=unused-argument
        calls.append(argv[0])
        return _Done(returncode=1 if argv[0].endswith("npm") else 0)

    with pytest.raises(RuntimeError, match="npm"):
        maintain.upgrade_clis(
            commands,
            {"PATH": ""},
            run=fake_run,
            which=lambda name, path=None: f"/bin/{name}",
            emit=lambda _: None,
        )

    assert calls == ["/bin/npm", "/bin/pi"]


# --- versions ----------------------------------------------------------------


def test_a_missing_command_has_no_version():
    assert maintain.version("definitely-not-installed-xyz") == "n/a"


def test_a_present_command_reports_its_first_output_line():
    assert maintain.version("git").startswith("git version")


# --- worktree guard ----------------------------------------------------------


def test_a_linked_worktree_is_detected_and_the_main_checkout_is_not(remote, tmp_path):
    _, clone = remote
    linked = tmp_path / "linked"
    _git(clone, "worktree", "add", "-b", "other", str(linked))

    assert maintain.is_linked_worktree(linked)
    assert not maintain.is_linked_worktree(clone)
