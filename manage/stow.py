"""The stow job: mirroring this repo's stow packages into the home directory.

Stowing is one of the two jobs CONTEXT.md names, and this is all of it bar the
shared skills hub, which owns its own stow-out. `StowPlan` holds what to stow and
where, and delegates the mirroring itself to the dploy library.
"""

import contextlib
import os
import pathlib

from manage import repo
from manage.agents import skills_hub


@contextlib.contextmanager
def tolerating_windows_symlink_failure(what):
    """Skip a stow-shaped operation that failed for want of Windows privilege.

    Creating a symlink on Windows is privilege-gated, so any stow-shaped
    operation aborts on an unelevated shell without Developer Mode -- see
    docs/gotchas/windows-symlink-creation-needs-elevation.md. That is a property
    of the machine rather than of the checkout, so on Windows the failure is
    reported and swallowed; everywhere else it is a real bug and re-raised.

    This is the one place the tolerate-on-Windows decision is made. Every
    stow-shaped task wraps its body in it rather than repeating the catch, so a
    task added later inherits the policy. `what` names the operation for the
    skip message.
    """
    # File-level import for the same reason StowPlan imports dploy late: this
    # module must be importable before provisioning has installed dploy.
    from dploy.error import DployError  # pylint: disable=import-outside-toplevel

    try:
        yield
    except (OSError, DployError) as error:
        if not repo.IS_WINDOWS:
            raise
        print(f"Skipping {what} on Windows: {error}")

# Directories that must already exist as real directories when stowing starts.
# dploy folds a fully-owned directory into a single symlink, and folding high
# swallows paths that must stay real:
#
# Claude Code writes far more into ~/.claude than the two files this repo stows
# there: .credentials.json, session and project history, caches. The claude-code
# stow package supplies only CLAUDE.md and output-styles/, so on a machine where
# ~/.claude does not exist yet the whole directory folds into one symlink into
# this repo and every one of those lands in a public working tree.
#
# pi writes runtime state into ~/.pi/agent/ during normal use -- npm package
# payloads, per-project trust.json decisions carrying real local paths and
# project names, session history. Without ~/.pi in place, stowing folds the
# whole directory into one symlink into this repo, landing that state inside
# the working tree of a repo that is public on GitHub.
#
# ~/.config/ai-instructions is where a dotfiles_local repo drops a private
# local.md beside these fragments, and the generated instruction files tell
# every agent to read it. Folding would put that private file in this public
# repo.
#
# Three parties write into ~/.pi/agent/extensions/: this repo, a dotfiles_local
# repo's per-file extension links, and pi's own package installers, which
# git-clone a package straight into extensions/<package>/ and write config back
# there. Every one of those writes lands in this public repo's working tree if
# the directory folds into a symlink. subagent/ is named because pi-subagents is
# currently the only package directory we own config inside; add a sibling here
# when we own config in another.
#
# herdr keeps its running server's state next to its config in ~/.config/herdr:
# two unix sockets, two logs, and a session.json naming every open workspace,
# tab, and cwd. This repo stows only config.toml there, so folding would put a
# live server's sockets and session layout in this public repo's working tree.
#
# ~/.config/ai-knowledge is the agent-knowledge equivalent of ai-instructions:
# this repo stows bundles.yaml there, and on a work machine a dotfiles_local repo
# adds bundles_local.yaml beside it. Folding would land that private file -- work
# bundle names, paths, and activation roots -- in this public repo.
#
# ~/.claude/plugins and ~/.config/opencode/plugins each hold one plugin of ours
# beside whatever else is installed: Claude Code clones marketplace plugins into
# the former, and a dotfiles_local repo owns opencode.jsonc next to the latter.
#
# The shared skills hub needs the same treatment for a different reason; its
# barrier and the ADR behind it live in manage.agents.skills_hub.
_FOLD_BARRIERS = (
    pathlib.PurePath(".claude"),
    pathlib.PurePath(".claude/plugins"),
    pathlib.PurePath(".pi"),
    pathlib.PurePath(".pi/agent"),
    pathlib.PurePath(".pi/agent/extensions"),
    pathlib.PurePath(".pi/agent/extensions/subagent"),
    pathlib.PurePath(".config/ai-instructions"),
    pathlib.PurePath(".config/ai-knowledge"),
    pathlib.PurePath(".config/herdr"),
    pathlib.PurePath(".config/opencode"),
    pathlib.PurePath(".config/opencode/plugins"),
)

_STOW_PACKAGES = [
    "agents",
    "claude-code",
    "ctags",
    "git",
    "herdr",
    "neovide",
    "opencode",
    "pi",
    "readline",
    "scripts",
    "shell",
    "ssh",
    "tmux",
    "nvim",
    "wezterm",
    "zsh",
]

_WINDOWS_ONLY_STOW_PACKAGES = ["powershell", "vcxsrv"]


class StowPlan:
    """What to stow and where, plus the stow, unstow and clean operations.

    Constructing it has side effects: it decides which explicit links apply on
    this machine, and creates the `files` tree when Dropbox is absent.
    """

    def __init__(self):
        # File-level import so this module does not depend on dploy being
        # installed, which would prevent provisioning from installing it.
        import dploy  # pylint: disable=import-outside-toplevel

        self.dploy = dploy
        self.home = pathlib.Path.home()
        self.stow_packages = list(_STOW_PACKAGES)
        if repo.IS_WINDOWS:
            self.stow_packages.extend(_WINDOWS_ONLY_STOW_PACKAGES)

        self.links = []

        dropbox = self.home / "Dropbox"
        files = self.home / "files"
        if dropbox.exists():
            self.links.append((dropbox, files))
        else:
            # No Dropbox to link to, so the tree it would have provided is
            # created empty rather than left missing.
            for area in ("documents", "projects", "notes"):
                path = files / area / "archive"
                path.mkdir(parents=True, exist_ok=True)
                print(f"Creating Directory {path}")

        if repo.IS_WINDOWS:
            self.links += [
                (self.home / ".config/nvim", self.home / "AppData/Local/nvim"),
                (self.home / ".config/neovide", self.home / "AppData/Roaming/neovide"),
            ]

    def pre_create(self):
        """Create every directory that must stay real before dploy folds."""
        skills_hub.pre_create(self.home)
        for barrier in _FOLD_BARRIERS:
            (self.home / barrier).mkdir(parents=True, exist_ok=True)

    def stow(self):
        """Mirror every stow package into the home directory, then apply links.

        Package names stay relative: dploy derives each symlink's target from
        the source path it is given, so absolute paths here would rewrite every
        existing link. The caller's working directory must be the repo root.
        """
        print(self.stow_packages)
        self.pre_create()
        self.dploy.stow(self.stow_packages, self.home, is_silent=False)
        for src, dest in self.links:
            self.dploy.link(src, dest, is_silent=False)

    def unstow(self):
        """Remove every link, then unstow every stow package."""
        for _, dest in reversed(self.links):
            try:
                os.unlink(dest)
            except FileNotFoundError:
                pass

        self.dploy.unstow(self.stow_packages, self.home, is_silent=False)

    def clean(self):
        """Remove dead symlinks left over from stowing.

        Replaces dploy's own clean sub-command, which traverses the entire stow
        destination and chokes on permission-denied entries along the way (a
        frequent failure on Windows). This walk is depth-limited to the deepest
        package path, skips EXCLUDE_DIRS, and swallows PermissionError.

        Shares the stow call's working-directory assumption: package names are
        relative, so the depth is measured from the repo root.
        """
        max_depth = max(
            len(p.relative_to(pkg).parts)
            for pkg in self.stow_packages
            for p in pathlib.Path(pkg).rglob("*")
        )
        _clean_dead_links(self.home, repo.ROOT, max_depth)


# Windows readlink() returns the reparse point's substitute name, which carries
# an extended-length prefix: \\?\ , or \??\ for the NT object path form. A path
# built from one never compares equal to a path built normally, so without
# stripping it the sweep below silently matches nothing on Windows and no dead
# link is ever removed there. See
# docs/gotchas/windows-readlink-returns-an-extended-length-path.md
_EXTENDED_PATH_PREFIXES = ("\\\\?\\", "\\??\\")


def _strip_extended_prefix(target):
    """Drop any Windows extended-length prefix from a raw readlink() result."""
    for prefix in _EXTENDED_PATH_PREFIXES:
        if target.startswith(prefix):
            return target[len(prefix) :]
    return target


def _link_target(entry):
    """The absolute path a symlink points at, comparable across platforms."""
    raw = _strip_extended_prefix(os.fspath(entry.readlink()))
    return (entry.parent / raw).resolve()


def _clean_dead_links(directory, repo_dir, max_depth, current_depth=0):
    """Recursively remove dead symlinks pointing into this repo.

    Limited by depth, skipping EXCLUDE_DIRS and permission-denied directories.
    Only links resolving inside `repo_dir` are removed, so another tool's broken
    links are left alone.
    """
    if current_depth > max_depth:
        return

    try:
        entries = list(directory.iterdir())
    except PermissionError:
        return

    for entry in entries:
        if entry.is_symlink():
            target = _link_target(entry)
            if not target.exists() and repo_dir in target.parents:
                print(f"removing dead link: {entry}")
                entry.unlink()
        elif entry.is_dir() and not entry.is_symlink():
            if entry.name in repo.EXCLUDE_DIRS:
                continue
            _clean_dead_links(entry, repo_dir, max_depth, current_depth + 1)
