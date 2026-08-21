"""Tests for the stow job: the fold barriers and the dead-link sweep.

The fold-barrier tests mirror tests/test_skills_hub.py. Both assert the same
dploy behaviour from opposite sides -- the hub needs folding constrained so two
repos can share a directory, while ~/.pi and ~/.config/ai-instructions need it
constrained so runtime state and a private file never land in this public repo.
A dploy upgrade should be re-tested against both.
"""

# Test names document each case, and the helpers are private to the module.
# pylint: disable=missing-function-docstring,protected-access

import pathlib

import pytest

from manage import stow

dploy = pytest.importorskip("dploy")


@pytest.fixture(name="home")
def fixture_home(tmp_path, monkeypatch):
    """A fake $HOME, so constructing StowPlan cannot touch the real one."""
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setattr(pathlib.Path, "home", classmethod(lambda cls: home))
    return home


# --- the fold barriers -------------------------------------------------------


def _pi_source(base):
    """A stow package contributing ~/.pi/agent/settings.json, as `pi` does."""
    package = base / "pi"
    agent = package / ".pi" / "agent"
    agent.mkdir(parents=True)
    (agent / "settings.json").write_text("{}\n")
    return package


def test_without_the_barrier_dploy_folds_the_whole_pi_directory(tmp_path):
    """Establishes the failure the barrier prevents; if this stops holding, the
    barrier may no longer be needed."""
    home = tmp_path / "home"
    home.mkdir()
    dploy.stow([_pi_source(tmp_path / "src")], home, is_silent=True)
    assert (home / ".pi").is_symlink()


def test_the_barrier_keeps_pi_a_real_directory(tmp_path):
    home = tmp_path / "home"
    home.mkdir()
    for barrier in stow._FOLD_BARRIERS:
        (home / barrier).mkdir(parents=True, exist_ok=True)

    dploy.stow([_pi_source(tmp_path / "src")], home, is_silent=True)

    assert (home / ".pi").is_dir() and not (home / ".pi").is_symlink()
    assert (home / ".pi" / "agent").is_dir()
    assert not (home / ".pi" / "agent").is_symlink()
    assert (home / ".pi" / "agent" / "settings.json").exists()


def test_runtime_state_beside_a_stowed_file_stays_out_of_the_source_tree(tmp_path):
    """The reason the barrier exists: pi writes into ~/.pi/agent during use."""
    home = tmp_path / "home"
    home.mkdir()
    source = _pi_source(tmp_path / "src")
    for barrier in stow._FOLD_BARRIERS:
        (home / barrier).mkdir(parents=True, exist_ok=True)
    dploy.stow([source], home, is_silent=True)

    (home / ".pi" / "agent" / "trust.json").write_text("{}\n")

    assert not (source / ".pi" / "agent" / "trust.json").exists()


def test_pre_create_makes_every_barrier_a_real_directory(home):
    stow.StowPlan().pre_create()

    for barrier in stow._FOLD_BARRIERS:
        assert (home / barrier).is_dir()
        assert not (home / barrier).is_symlink()


def test_pre_create_includes_the_shared_skills_hub(home):
    stow.StowPlan().pre_create()

    assert (home / ".config" / "ai-skills" / "skills").is_dir()


def test_pre_create_is_repeatable(home):
    stow.StowPlan().pre_create()
    stow.StowPlan().pre_create()

    assert (home / ".pi" / "agent").is_dir()


# --- constructing StowPlan ------------------------------------------------------


def test_the_files_tree_is_created_when_dropbox_is_absent(home):
    stow.StowPlan()

    for area in ("documents", "projects", "notes"):
        assert (home / "files" / area / "archive").is_dir()


def test_dropbox_is_linked_to_files_when_present(home):
    (home / "Dropbox").mkdir()

    plan = stow.StowPlan()

    assert (home / "Dropbox", home / "files") in plan.links
    assert not (home / "files").exists()


@pytest.mark.usefixtures("home")
def test_the_stow_package_list_is_not_shared_between_instances():
    first = stow.StowPlan()
    first.stow_packages.append("scratch")

    assert "scratch" not in stow.StowPlan().stow_packages


# --- the dead-link sweep -----------------------------------------------------


def _sweep(home, repo_dir, depth=5):
    stow._clean_dead_links(home, repo_dir, depth)


def test_a_dead_link_into_the_repo_is_removed(tmp_path):
    home, repo_dir = tmp_path / "home", tmp_path / "repo"
    home.mkdir()
    repo_dir.mkdir()
    (home / ".gone").symlink_to(repo_dir / "gone")

    _sweep(home, repo_dir)

    assert not (home / ".gone").is_symlink()


def test_a_live_link_into_the_repo_is_kept(tmp_path):
    home, repo_dir = tmp_path / "home", tmp_path / "repo"
    home.mkdir()
    repo_dir.mkdir()
    (repo_dir / "real").write_text("x")
    (home / ".real").symlink_to(repo_dir / "real")

    _sweep(home, repo_dir)

    assert (home / ".real").is_symlink()


def test_a_dead_link_pointing_elsewhere_is_left_alone(tmp_path):
    """Another tool's broken link is not this sweep's business."""
    home, repo_dir = tmp_path / "home", tmp_path / "repo"
    home.mkdir()
    repo_dir.mkdir()
    (home / ".foreign").symlink_to(tmp_path / "somewhere-else")

    _sweep(home, repo_dir)

    assert (home / ".foreign").is_symlink()


def test_the_sweep_descends_into_subdirectories(tmp_path):
    home, repo_dir = tmp_path / "home", tmp_path / "repo"
    (home / ".config" / "deep").mkdir(parents=True)
    repo_dir.mkdir()
    (home / ".config" / "deep" / "gone").symlink_to(repo_dir / "gone")

    _sweep(home, repo_dir)

    assert not (home / ".config" / "deep" / "gone").is_symlink()


def test_the_sweep_stops_at_the_depth_limit(tmp_path):
    home, repo_dir = tmp_path / "home", tmp_path / "repo"
    (home / "a" / "b" / "c").mkdir(parents=True)
    repo_dir.mkdir()
    (home / "a" / "b" / "c" / "gone").symlink_to(repo_dir / "gone")

    stow._clean_dead_links(home, repo_dir, 1)

    assert (home / "a" / "b" / "c" / "gone").is_symlink()


def test_excluded_directories_are_not_walked(tmp_path):
    home, repo_dir = tmp_path / "home", tmp_path / "repo"
    (home / ".git").mkdir(parents=True)
    repo_dir.mkdir()
    (home / ".git" / "gone").symlink_to(repo_dir / "gone")

    _sweep(home, repo_dir)

    assert (home / ".git" / "gone").is_symlink()


# --- Windows link targets ----------------------------------------------------
#
# Runnable on any platform because the normalisation is a string operation: the
# bug it prevents only reproduces on Windows, where readlink() is what produces
# these prefixes.


def test_the_extended_length_prefix_is_stripped():
    assert (
        stow._strip_extended_prefix(r"\\?\C:\Users\x\repo\gone")
        == r"C:\Users\x\repo\gone"
    )


def test_the_nt_object_path_prefix_is_stripped():
    assert stow._strip_extended_prefix(r"\??\C:\Users\x\repo") == r"C:\Users\x\repo"


def test_a_plain_windows_path_is_left_alone():
    assert stow._strip_extended_prefix(r"C:\Users\x\repo") == r"C:\Users\x\repo"


def test_a_posix_path_is_left_alone():
    assert stow._strip_extended_prefix("/home/x/repo/gone") == "/home/x/repo/gone"


def test_the_barrier_keeps_the_claude_directory_real(tmp_path):
    """Claude Code writes credentials and session history into ~/.claude, and
    the stow package supplies only two entries, so folding would put all of it
    in this public repo."""
    home = tmp_path / "home"
    home.mkdir()
    package = tmp_path / "src" / "claude-code"
    (package / ".claude" / "output-styles").mkdir(parents=True)
    (package / ".claude" / "CLAUDE.md").write_text("x")
    for barrier in stow._FOLD_BARRIERS:
        (home / barrier).mkdir(parents=True, exist_ok=True)

    dploy.stow([package], home, is_silent=True)

    assert (home / ".claude").is_dir() and not (home / ".claude").is_symlink()
    assert (home / ".claude" / "CLAUDE.md").is_symlink()

    # What Claude Code writes afterwards stays out of the source tree.
    (home / ".claude" / ".credentials.json").write_text("{}\n")
    assert not (package / ".claude" / ".credentials.json").exists()


def test_without_the_barrier_the_claude_directory_folds(tmp_path):
    """Establishes the failure the barrier prevents."""
    home = tmp_path / "home"
    home.mkdir()
    package = tmp_path / "src" / "claude-code"
    (package / ".claude").mkdir(parents=True)
    (package / ".claude" / "CLAUDE.md").write_text("x")

    dploy.stow([package], home, is_silent=True)

    assert (home / ".claude").is_symlink()
