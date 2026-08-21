"""The shared skills hub: where it lives, and how it reaches each agent tool.

The hub is the directory where shared skills from several repos are collected,
so one copy serves every tool. Two separate stows touch it. Repos contribute
into it by stowing their own `agents` stow package, which is what `pre_create`
constrains; `stow_out` then mirrors the result into each tool's skills
discovery path.

Every path the hub occupies is derived here and nowhere else. `home` is a
parameter throughout so the whole module can be exercised against a temporary
directory; passing None means the real home directory.
"""

import pathlib

# Relative to the home directory, so a test can supply its own.
_ROOT = pathlib.PurePath(".config/ai-skills")
_SKILLS = "skills"

# Every agent tool reads its skills from its own directory. Adding a third tool
# means adding one entry here.
_DISCOVERY_PATHS = (
    pathlib.PurePath(".claude"),
    pathlib.PurePath(".config/opencode"),
    pathlib.PurePath(".pi/agent"),
)

# plugins.yaml sits beside the skills in the same stow package but is not a
# skill, so it is not mirrored out to the tools.
_NOT_SKILLS = ["*.yaml"]


def _home(home):
    return pathlib.Path.home() if home is None else pathlib.Path(home)


def root(home=None):
    """The hub directory itself."""
    return _home(home) / _ROOT


def skills_dir(home=None):
    """The hub's `skills` child, which holds one entry per shared skill."""
    return root(home) / _SKILLS


def discovery_paths(home=None):
    """Each agent tool's skills discovery path, in stow order."""
    return [_home(home) / p for p in _DISCOVERY_PATHS]


def pre_create(home=None):
    """Create the hub and its `skills` child as real directories.

    Load-bearing despite looking like dead code -- stowing would create both
    anyway. It constrains where dploy is allowed to fold: this repo and
    dotfiles_local both carry an `agents` stow package, so two independent dploy
    runs write here. Without real directories in place the first run folds high,
    at `~/.config`, and the second unfolds one level too shallow and writes
    dangling links inside the first repo's working tree. With them, folding can
    only happen at `skills`, where dploy's unfold computes the right paths.

    See docs/adr/0001-pre-create-the-shared-skills-hub.md, which also records
    that this was established experimentally against dploy 0.1.3 -- the folding
    behaviour is undocumented, so a dploy upgrade should be re-tested rather
    than assumed compatible. tests/test_skills_hub.py is that test.
    """
    root(home).mkdir(parents=True, exist_ok=True)
    skills_dir(home).mkdir(parents=True, exist_ok=True)


def _clear_blocked_destination(path):
    """Remove any dangling symlink at `path` or directly inside it.

    A precondition for stowing into `path`: dploy cannot stow into a destination
    that is itself a dangling symlink, nor past one of its entries. Both arise
    when a skill or the hub itself moves, leaving links to the old location.
    """
    if path.is_symlink() and not path.exists():
        path.unlink()
        return
    if path.is_dir():
        for entry in path.iterdir():
            if entry.is_symlink() and not entry.exists():
                entry.unlink()


def stow_out(home=None):
    """Stow the hub into every skills discovery path. No-op if the hub is absent.

    The hub is absent until some repo's `agents` stow package has been stowed,
    which on a fresh machine has not happened yet.
    """
    import dploy  # pylint: disable=import-outside-toplevel

    if not skills_dir(home).exists():
        return

    source = root(home)
    for target in discovery_paths(home):
        target.mkdir(parents=True, exist_ok=True)
        _clear_blocked_destination(target / _SKILLS)
        dploy.stow([source], target, is_silent=False, ignore_patterns=_NOT_SKILLS)
