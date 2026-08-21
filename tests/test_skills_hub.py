"""Tests for the shared skills hub, chiefly the ADR-0001 folding invariant.

ADR-0001 records that dploy's folding behaviour was established experimentally
against a specific dploy version rather than read out of its source, so a dploy
upgrade should be re-tested rather than assumed compatible. These tests are that
re-test: they stow two source trees that both contribute an `agents` stow
package into a temporary home, exactly as this repo and a dotfiles_local
checkout do on a work machine.
"""

# Test names document each case, and the helpers are private to the module.
# pylint: disable=missing-function-docstring,protected-access

import pytest

from manage.agents import skills_hub

dploy = pytest.importorskip("dploy")


def _source_tree(base, name, skills, manifest):
    """A source repo carrying an `agents` stow package with the given skills.

    `manifest` differs per tree the way the real ones do -- this repo ships
    plugins.yaml, a dotfiles_local checkout ships plugins_local.yaml -- so the
    two never collide in the hub.
    """
    package = base / name / "agents"
    hub = package / ".config" / "ai-skills"
    for skill in skills:
        skill_dir = hub / "skills" / skill
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text(f"# {skill}\n")
    (hub / manifest).write_text("{}\n")
    return package


@pytest.fixture(name="two_trees")
def fixture_two_trees(tmp_path):
    """A temporary home plus two source trees that both contribute skills."""
    home = tmp_path / "home"
    home.mkdir()
    sources = tmp_path / "src"
    first = _source_tree(sources, "dotfiles", ["a-skill"], "plugins.yaml")
    second = _source_tree(sources, "dotfiles_local", ["b-skill"], "plugins_local.yaml")
    return home, first, second


def _stow(home, *packages):
    """Stow each package into home the way Dploy.stow does, hub pre-create first."""
    for package in packages:
        skills_hub.pre_create(home)
        dploy.stow([package], home, is_silent=True)


def _dangling(root):
    return sorted(
        str(p.relative_to(root))
        for p in root.rglob("*")
        if p.is_symlink() and not p.exists()
    )


def _links_inside(tree):
    return sorted(str(p.relative_to(tree)) for p in tree.rglob("*") if p.is_symlink())


# --- the ADR-0001 invariant --------------------------------------------------


def test_stowing_both_trees_leaves_no_dangling_link_in_the_home(two_trees):
    home, first, second = two_trees
    _stow(home, first, second)
    assert _dangling(home) == []


def test_neither_tree_gains_a_link_from_stowing_the_other(two_trees):
    home, first, second = two_trees
    _stow(home, first, second)
    assert _links_inside(first) == []
    assert _links_inside(second) == []


def test_both_trees_skills_are_reachable_through_the_hub(two_trees):
    home, first, second = two_trees
    _stow(home, first, second)
    reachable = {p.name for p in skills_hub.skills_dir(home).iterdir()}
    assert {"a-skill", "b-skill"} <= reachable
    for name in ("a-skill", "b-skill"):
        assert (skills_hub.skills_dir(home) / name / "SKILL.md").exists()


def test_the_hub_and_its_skills_child_stay_real_directories(two_trees):
    home, first, second = two_trees
    _stow(home, first, second)
    assert skills_hub.root(home).is_dir() and not skills_hub.root(home).is_symlink()
    assert skills_hub.skills_dir(home).is_dir()


def test_folding_never_reaches_the_config_directory(two_trees):
    home, first, second = two_trees
    _stow(home, first, second)
    assert not (home / ".config").is_symlink()


# --- the full cycle ----------------------------------------------------------


def test_stow_unstow_restow_across_both_trees_ends_clean(two_trees):
    home, first, second = two_trees
    _stow(home, first, second)

    dploy.unstow([second], home, is_silent=True)
    dploy.unstow([first], home, is_silent=True)

    _stow(home, first, second)

    assert _dangling(home) == []
    assert _links_inside(first) == []
    assert _links_inside(second) == []
    assert (skills_hub.skills_dir(home) / "a-skill" / "SKILL.md").exists()
    assert (skills_hub.skills_dir(home) / "b-skill" / "SKILL.md").exists()


def test_unstowing_one_tree_leaves_the_others_skills_intact(two_trees):
    home, first, second = two_trees
    _stow(home, first, second)

    dploy.unstow([second], home, is_silent=True)

    assert _dangling(home) == []
    assert (skills_hub.skills_dir(home) / "a-skill" / "SKILL.md").exists()


def test_pre_create_tolerates_a_hub_folded_into_a_symlink(two_trees):
    """ADR-0001's self-healing consequence: unstowing one tree may re-fold
    `skills` into a symlink, and the next stow must recover rather than fail."""
    home, first, second = two_trees
    _stow(home, first, second)
    dploy.unstow([second], home, is_silent=True)

    skills_hub.pre_create(home)

    assert skills_hub.skills_dir(home).is_dir()


# --- stowing out to the discovery paths --------------------------------------


def test_stow_out_places_every_skill_in_every_discovery_path(two_trees):
    home, first, second = two_trees
    _stow(home, first, second)

    skills_hub.stow_out(home)

    for target in skills_hub.discovery_paths(home):
        for name in ("a-skill", "b-skill"):
            assert (target / "skills" / name / "SKILL.md").exists()


def test_stow_out_does_not_mirror_the_plugin_manifest(two_trees):
    home, first, second = two_trees
    _stow(home, first, second)

    skills_hub.stow_out(home)

    for target in skills_hub.discovery_paths(home):
        assert not (target / "plugins.yaml").exists()


def test_stow_out_is_a_no_op_when_the_hub_does_not_exist(tmp_path):
    skills_hub.stow_out(tmp_path)
    assert not any(p.exists() for p in skills_hub.discovery_paths(tmp_path))


def test_stow_out_replaces_a_discovery_path_left_dangling(two_trees):
    home, first, second = two_trees
    _stow(home, first, second)
    target = skills_hub.discovery_paths(home)[0]
    target.mkdir(parents=True, exist_ok=True)
    (target / "skills").symlink_to(home / "gone")

    skills_hub.stow_out(home)

    assert (target / "skills" / "a-skill" / "SKILL.md").exists()


def test_stow_out_is_repeatable(two_trees):
    home, first, second = two_trees
    _stow(home, first, second)

    skills_hub.stow_out(home)
    skills_hub.stow_out(home)

    assert _dangling(home) == []


# --- the paths ---------------------------------------------------------------


def test_the_skills_directory_is_a_child_of_the_hub(tmp_path):
    assert skills_hub.skills_dir(tmp_path).parent == skills_hub.root(tmp_path)


def test_every_discovery_path_is_under_the_given_home(tmp_path):
    paths = skills_hub.discovery_paths(tmp_path)
    assert paths
    assert all(p.is_relative_to(tmp_path) for p in paths)
