"""Which configured bundles apply here, and which project bundle to use.

Two independent questions, both answered from the current working directory:

- **Configured bundles** are declared by the user, so they activate on
  filesystem roots. Nothing is scanned for: a bundle applies only where its
  declaration says it does.
- **The project bundle** is repository-controlled, so it is discovered rather
  than declared -- and therefore gated by the user's `project_roots` allowlist.
  Discovery uses the *current worktree* root, so a feature worktree reads its
  own branch's knowledge instead of whatever the primary checkout holds.

Ordering runs broad to specific (always-active, then by matching-root depth,
then the project bundle), which is the order the rendered catalog states as
precedence.
"""

import os
import pathlib
import subprocess

from manage.knowledge import config, okf

PROJECT_DIR_NAME = "agents-knowledge"


def _canonical(path):
    """An absolute, symlink-free path, tolerating parts that do not exist."""
    return pathlib.Path(os.path.realpath(pathlib.Path(path).expanduser()))


def _contains(root, candidate):
    """Whether `candidate` is `root` or below it.

    Compared component-wise: a string prefix test would match `~/work-other`
    against a `~/work` root.
    """
    root, candidate = _canonical(root), _canonical(candidate)
    if os.path.normcase(str(root)) == os.path.normcase(str(candidate)):
        return True
    root_parts = [os.path.normcase(p) for p in root.parts]
    candidate_parts = [os.path.normcase(p) for p in candidate.parts]
    return candidate_parts[: len(root_parts)] == root_parts


def _match_depth(bundle, cwd):
    """Depth of the deepest activation root matching `cwd`, or None.

    The deepest match ranks the bundle: a bundle rooted at a specific project
    should outrank one covering the whole tree above it, whichever order they
    were declared in.
    """
    depths = [
        len(_canonical(root).parts) for root in bundle.roots if _contains(root, cwd)
    ]
    return max(depths) if depths else None


def active_bundles(bundles, cwd):
    """Configured bundles that apply in `cwd`, ordered broad to specific.

    Preserves declaration order among bundles of equal specificity, so output
    stays stable for tests, caching, and diffing.
    """
    always, rooted = [], []
    for index, bundle in enumerate(bundles):
        if bundle.always:
            always.append((index, bundle))
            continue
        depth = _match_depth(bundle, cwd)
        if depth is not None:
            rooted.append((depth, index, bundle))
    rooted.sort(key=lambda item: (item[0], item[1]))
    return [bundle for _, bundle in always] + [bundle for _, _, bundle in rooted]


def project_root(cwd):
    """The project root for `cwd`: the current worktree, else `cwd` itself.

    `--show-toplevel` reports the worktree containing `cwd` rather than the
    repository's primary checkout, which is what keeps branch-local knowledge
    branch-local. Outside git there is nothing to anchor to, so the directory
    itself is the root and no parent is searched.
    """
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=str(cwd),
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return _canonical(cwd)
    if result.returncode == 0 and result.stdout.strip():
        return _canonical(result.stdout.strip())
    return _canonical(cwd)


def project_bundle(cwd, project_roots):
    """The project bundle for `cwd`, or None when there is nothing to use.

    Returns None -- silently, as the normal case -- when no root is allowlisted,
    when the project is outside every allowlisted root, when the directory holds
    no bundle, or when the bundle is not usable. A repo-controlled symlink is
    refused: `agents-knowledge` and its index must be real entries inside the
    worktree, or a repository could redirect discovery at any readable path.
    """
    if not project_roots:
        return None

    root = project_root(cwd)
    if not any(_contains(allowed, root) for allowed in project_roots):
        return None

    bundle_dir = root / PROJECT_DIR_NAME
    index = bundle_dir / okf.INDEX_NAME
    if bundle_dir.is_symlink() or index.is_symlink():
        return None
    if not okf.is_bundle(bundle_dir):
        return None

    return config.Bundle(
        id=config.PROJECT_ID,
        name="Project knowledge",
        description="References for the current project",
        path=bundle_dir,
        always=False,
        roots=[],
    )
