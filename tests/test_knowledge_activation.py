"""Tests for deciding which bundles apply in a given working directory."""

# Test names document each case, and the helpers are private to the module.
# pylint: disable=missing-function-docstring
# Asserting == [] documents "no bundles" better than a falsiness check.
# pylint: disable=use-implicit-booleaness-not-comparison

import subprocess

from manage.knowledge import activation, config

OKF_INDEX = """\
---
okf_version: "0.2"
---
# Index

* [Thing](thing.md) - a thing
"""


def _bundle(path, bundle_id="b", always=False, roots=()):
    return config.Bundle(
        id=bundle_id,
        name=bundle_id,
        description="",
        path=path,
        always=always,
        roots=list(roots),
    )


def _okf_bundle(root, text=OKF_INDEX):
    root.mkdir(parents=True, exist_ok=True)
    (root / "index.md").write_text(text, encoding="utf-8")
    return root


def _git(cwd, *args):
    subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def _commit(path):
    _git(path, "add", "-A")
    _git(path, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q",
         "--allow-empty", "-m", "root")


def _repo(path):
    path.mkdir(parents=True, exist_ok=True)
    _git(path, "init", "-q")
    _commit(path)
    return path


# --- configured bundle activation ---------------------------------------------


def test_an_always_bundle_is_active_anywhere(tmp_path):
    bundle = _bundle(_okf_bundle(tmp_path / "kb"), always=True)

    assert activation.active_bundles([bundle], tmp_path / "anywhere") == [bundle]


def test_a_root_bundle_is_active_inside_its_root(tmp_path):
    work = tmp_path / "work"
    (work / "project").mkdir(parents=True)
    bundle = _bundle(_okf_bundle(tmp_path / "kb"), roots=[work])

    assert activation.active_bundles([bundle], work / "project") == [bundle]


def test_a_root_bundle_is_active_at_its_root(tmp_path):
    work = tmp_path / "work"
    work.mkdir()
    bundle = _bundle(_okf_bundle(tmp_path / "kb"), roots=[work])

    assert activation.active_bundles([bundle], work) == [bundle]


def test_a_root_bundle_is_inactive_elsewhere(tmp_path):
    (tmp_path / "work").mkdir()
    (tmp_path / "personal").mkdir()
    bundle = _bundle(_okf_bundle(tmp_path / "kb"), roots=[tmp_path / "work"])

    assert activation.active_bundles([bundle], tmp_path / "personal") == []


def test_a_sibling_sharing_a_name_prefix_does_not_activate(tmp_path):
    """`~/work-other` is not inside `~/work`; matching is by path component."""
    (tmp_path / "work").mkdir()
    (tmp_path / "work-other").mkdir()
    bundle = _bundle(_okf_bundle(tmp_path / "kb"), roots=[tmp_path / "work"])

    assert activation.active_bundles([bundle], tmp_path / "work-other") == []


def test_any_matching_root_activates_a_bundle(tmp_path):
    (tmp_path / "a").mkdir()
    (tmp_path / "b").mkdir()
    bundle = _bundle(
        _okf_bundle(tmp_path / "kb"), roots=[tmp_path / "a", tmp_path / "b"]
    )

    assert activation.active_bundles([bundle], tmp_path / "b") == [bundle]


def test_a_symlinked_working_directory_is_canonicalised(tmp_path):
    work = tmp_path / "work"
    work.mkdir()
    link = tmp_path / "link"
    link.symlink_to(work)
    bundle = _bundle(_okf_bundle(tmp_path / "kb"), roots=[work])

    assert activation.active_bundles([bundle], link) == [bundle]


# --- ordering -----------------------------------------------------------------


def test_always_bundles_precede_root_bundles(tmp_path):
    work = tmp_path / "work"
    work.mkdir()
    everywhere = _bundle(_okf_bundle(tmp_path / "kb1"), "everywhere", always=True)
    here = _bundle(_okf_bundle(tmp_path / "kb2"), "here", roots=[work])

    active = activation.active_bundles([here, everywhere], work)

    assert [b.id for b in active] == ["everywhere", "here"]


def test_shallower_roots_precede_deeper_roots(tmp_path):
    broad_root = tmp_path / "work"
    narrow_root = broad_root / "team" / "project"
    narrow_root.mkdir(parents=True)
    broad = _bundle(_okf_bundle(tmp_path / "kb1"), "broad", roots=[broad_root])
    narrow = _bundle(_okf_bundle(tmp_path / "kb2"), "narrow", roots=[narrow_root])

    active = activation.active_bundles([narrow, broad], narrow_root)

    assert [b.id for b in active] == ["broad", "narrow"]


def test_a_bundle_is_ranked_by_its_deepest_matching_root(tmp_path):
    shallow = tmp_path / "work"
    deep = shallow / "team"
    deep.mkdir(parents=True)
    both = _bundle(_okf_bundle(tmp_path / "kb1"), "both", roots=[shallow, deep])
    other = _bundle(_okf_bundle(tmp_path / "kb2"), "other", roots=[shallow])

    active = activation.active_bundles([both, other], deep)

    assert [b.id for b in active] == ["other", "both"]


def test_declaration_order_breaks_ties_at_equal_depth(tmp_path):
    work = tmp_path / "work"
    work.mkdir()
    first = _bundle(_okf_bundle(tmp_path / "kb1"), "first", roots=[work])
    second = _bundle(_okf_bundle(tmp_path / "kb2"), "second", roots=[work])

    active = activation.active_bundles([first, second], work)

    assert [b.id for b in active] == ["first", "second"]


# --- project discovery --------------------------------------------------------


def test_a_project_bundle_is_discovered_at_the_worktree_root(tmp_path):
    repo = _repo(tmp_path / "repo")
    _okf_bundle(repo / "agents-knowledge")

    found = activation.project_bundle(repo, [tmp_path])

    assert found.path == repo / "agents-knowledge"
    assert found.id == config.PROJECT_ID


def test_a_project_bundle_is_found_from_a_subdirectory(tmp_path):
    repo = _repo(tmp_path / "repo")
    _okf_bundle(repo / "agents-knowledge")
    (repo / "src" / "deep").mkdir(parents=True)

    found = activation.project_bundle(repo / "src" / "deep", [tmp_path])

    assert found.path == repo / "agents-knowledge"


def test_a_linked_worktree_uses_its_own_branch_local_bundle(tmp_path):
    """A feature worktree must not read the primary checkout's knowledge."""
    repo = _repo(tmp_path / "repo")
    _okf_bundle(repo / "agents-knowledge")
    _commit(repo)
    tree = tmp_path / "tree"
    _git(repo, "worktree", "add", "-q", str(tree), "-b", "feature")
    (tree / "agents-knowledge" / "index.md").write_text(
        OKF_INDEX.replace("a thing", "branch thing"), encoding="utf-8"
    )

    found = activation.project_bundle(tree, [tmp_path])

    assert found.path == tree / "agents-knowledge"


def test_a_worktree_without_the_directory_has_no_project_bundle(tmp_path):
    repo = _repo(tmp_path / "repo")

    assert activation.project_bundle(repo, [tmp_path]) is None


def test_outside_git_the_exact_directory_is_the_project_root(tmp_path):
    plain = tmp_path / "plain"
    _okf_bundle(plain / "agents-knowledge")

    assert activation.project_bundle(plain, [tmp_path]).path == plain / "agents-knowledge"


def test_outside_git_a_parent_directory_is_not_searched(tmp_path):
    plain = tmp_path / "plain"
    _okf_bundle(plain / "agents-knowledge")
    (plain / "child").mkdir()

    assert activation.project_bundle(plain / "child", [tmp_path]) is None


def test_a_project_outside_the_allowlist_is_not_discovered(tmp_path):
    repo = _repo(tmp_path / "elsewhere" / "repo")
    _okf_bundle(repo / "agents-knowledge")

    assert activation.project_bundle(repo, [tmp_path / "approved"]) is None


def test_no_project_roots_disables_project_discovery(tmp_path):
    repo = _repo(tmp_path / "repo")
    _okf_bundle(repo / "agents-knowledge")

    assert activation.project_bundle(repo, []) is None


def test_a_symlinked_project_bundle_is_refused(tmp_path):
    """Repository-controlled symlinks must not pull in knowledge from outside
    the worktree, so the directory itself has to be real."""
    repo = _repo(tmp_path / "repo")
    outside = _okf_bundle(tmp_path / "outside")
    (repo / "agents-knowledge").symlink_to(outside)

    assert activation.project_bundle(repo, [tmp_path]) is None


def test_a_symlinked_project_index_is_refused(tmp_path):
    repo = _repo(tmp_path / "repo")
    outside = _okf_bundle(tmp_path / "outside")
    (repo / "agents-knowledge").mkdir()
    (repo / "agents-knowledge" / "index.md").symlink_to(outside / "index.md")

    assert activation.project_bundle(repo, [tmp_path]) is None
