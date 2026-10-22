"""Routine upkeep of the agent tooling: pull the dotfiles, upgrade the CLIs.

The pieces here are the ones with logic worth testing. Running the existing
plugin and stow tasks is `tasks.maintain`'s job; this module never prompts for
sudo, which is why the CLI upgrades read ansible's package lists and run the
same user-level commands instead of invoking the playbook.
"""

import dataclasses
import pathlib
import subprocess

# Run order. `--only`/`--skip` select from these and never reorder them.
GROUPS = ["pull", "cli", "plugins", "stow", "local"]

# Mirrors ansible/group_vars/all.yml (npm_prefix_subpath) and the pnpm_bin_dir
# in ansible/tasks/javascript-packages.yml; change them together.
NPM_PREFIX_SUBPATH = ".local"
PNPM_HOME_SUBPATH = pathlib.Path(".local") / "share" / "pnpm"


@dataclasses.dataclass(frozen=True)
class PullResult:
    """Outcome of pulling one repo.

    status is "current", "updated", "skipped" or "missing". `detail` carries
    git's own refusal message when skipped, so the report says why.
    """

    status: str
    detail: str = ""


@dataclasses.dataclass(frozen=True)
class Command:
    """A command to run and the environment it needs on top of the caller's."""

    argv: list[str]
    env: dict[str, str]


def _git(repo, *args):
    return subprocess.run(
        ["git", *args], cwd=repo, check=False, capture_output=True, text=True
    )


def pull(repo):
    """Fast-forward `repo` from its upstream; never stash, merge or rewrite.

    `--ff-only` already refuses when an incoming change would overwrite a
    local edit and when history has diverged, and it leaves unrelated local
    edits alone. So a dirty tree is pulled when git allows it and skipped when
    git refuses, with git's message kept as the reason.
    """
    repo = pathlib.Path(repo)
    if not (repo / ".git").exists():
        return PullResult("missing", f"{repo} is not a git checkout")

    before = _git(repo, "rev-parse", "HEAD").stdout.strip()
    result = _git(repo, "pull", "--ff-only")
    if result.returncode != 0:
        return PullResult("skipped", (result.stderr or result.stdout).strip())
    after = _git(repo, "rev-parse", "HEAD").stdout.strip()
    return PullResult("current" if before == after else "updated")


def select_groups(only="", skip=""):
    """Return the groups to run, in run order, from comma-separated `only`/`skip`.

    An empty `only` means all groups. A name outside GROUPS is an error rather
    than silently ignored, so a typo cannot skip a step unnoticed.
    """
    wanted = [g.strip() for g in only.split(",") if g.strip()]
    dropped = [g.strip() for g in skip.split(",") if g.strip()]
    unknown = sorted(set(wanted + dropped) - set(GROUPS))
    if unknown:
        raise ValueError(f"unknown group(s): {', '.join(unknown)}; choose from {', '.join(GROUPS)}")
    keep = set(wanted) if wanted else set(GROUPS)
    return [g for g in GROUPS if g in keep and g not in dropped]


def cli_commands(group_vars, home):
    """Commands that upgrade Claude Code and pi without sudo.

    `group_vars` is the parsed ansible/group_vars/all.yml, so the package list
    has one home. Claude Code is npm-managed under the user prefix (see
    ansible/tasks/npm-packages.yml). pi updates itself through pnpm, which only
    works with PNPM_HOME set and on PATH -- the failure `pi update --self`
    reports otherwise.
    """
    home = pathlib.Path(home)
    npm_env = {"NPM_CONFIG_PREFIX": str(home / NPM_PREFIX_SUBPATH)}
    commands = [
        Command(["npm", "install", "-g", f"{package}@latest"], npm_env)
        for package in group_vars.get("npm_global_packages", [])
    ]

    pnpm_home = str(home / PNPM_HOME_SUBPATH)
    commands.append(
        Command(["pi", "update", "--self"], {"PNPM_HOME": pnpm_home, "PATH": pnpm_home})
    )
    return commands


def is_linked_worktree(path):
    """True when `path` is a linked git worktree rather than a main checkout.

    Stowing from a linked worktree points the home-directory symlinks into it,
    and they dangle once it is removed, so the stow group refuses to run there.
    """
    git_dir = _git(path, "rev-parse", "--path-format=absolute", "--git-dir").stdout.strip()
    common = _git(path, "rev-parse", "--path-format=absolute", "--git-common-dir").stdout.strip()
    return git_dir != common
