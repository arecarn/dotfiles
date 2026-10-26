"""Routine upkeep of the agent tooling: pull the dotfiles, upgrade the CLIs.

Everything with logic worth testing lives here; `tasks.maintain` only supplies
the runners and prints. Nothing here prompts for sudo: the CLI upgrades read
ansible's package settings and run the same user-level commands instead of
invoking the playbook.
"""

import dataclasses
import os
import pathlib
import shutil
import subprocess

# Run order. `--only`/`--skip` select from these and never reorder them.
GROUPS = ["pull", "cli", "plugins", "stow", "local"]

# The pnpm home ansible/tasks/javascript-packages.yml uses (`pnpm_bin_dir`).
# Unlike the npm prefix, no group_vars key holds it, so it is the one value
# here that must change in step with that file.
PNPM_HOME_SUBPATH = pathlib.Path(".local") / "share" / "pnpm"
DEFAULT_NPM_PREFIX_SUBPATH = ".local"

# The checkouts `pull` updates. Dotfiles is first and gates `stow`.
CHECKOUTS = ["dotfiles", "dotfiles_local"]


@dataclasses.dataclass(frozen=True)
class PullResult:
    """Outcome of pulling one repo.

    status is "current", "updated", "skipped" or "missing". `detail` carries
    git's own refusal message when skipped, so the report says why.
    """

    status: str
    detail: str = ""


@dataclasses.dataclass(frozen=True)
class Outcome:
    """What one group did.

    status is "ok", "partial" (ran, but something was skipped), "skipped"
    (never ran) or "FAILED". `blocks` marks a result later groups depend on
    (a `pull` that left dotfiles stale), so `run_groups` can skip them.
    """

    status: str
    detail: str = ""
    blocks: bool = False


@dataclasses.dataclass(frozen=True)
class Command:
    """A command to run, the environment it needs, and a PATH entry to put first."""

    argv: list[str]
    env: dict[str, str] = dataclasses.field(default_factory=dict)
    prepend_path: str = ""


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


def pull_group(home):
    """Pull each of CHECKOUTS under `home`; the detail lists every repo's result.

    Partial when any repo was skipped or missing, and blocking when that repo is
    the first (dotfiles), since restowing a stale checkout links stale files.
    """
    parts = []
    problems = []
    blocks = False
    for index, name in enumerate(CHECKOUTS):
        result = pull(pathlib.Path(home) / name)
        reason = f" ({result.detail})" if result.detail else ""
        parts.append(f"{name}: {result.status}{reason}")
        if result.status in ("skipped", "missing"):
            problems.append(name)
            blocks = blocks or index == 0
    return Outcome("partial" if problems else "ok", "; ".join(parts), blocks)


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


def cli_commands(group_vars, home, windows=False):
    """Commands that upgrade Claude Code and pi without sudo.

    `group_vars` is the parsed ansible/group_vars/all.yml, so Claude Code's
    package and the npm prefix have one home. On Linux the prefix and PNPM_HOME
    are set explicitly: without them npm falls back to a system prefix and pi's
    updater reports a missing global bin directory. On Windows neither problem
    exists, so the user's own npm and pnpm configuration is left alone.

    pi is updated by its own updater, not from the pnpm package list: it is the
    documented path, and it knows what the installed pi is.
    """
    home = pathlib.Path(home)
    env = {}
    if not windows:
        prefix = group_vars.get("npm_prefix_subpath", DEFAULT_NPM_PREFIX_SUBPATH)
        env = {"NPM_CONFIG_PREFIX": str(home / prefix)}
    commands = [
        Command(["npm", "install", "-g", f"{package}@latest"], dict(env))
        for package in group_vars.get("npm_global_packages", [])
    ]

    if windows:
        commands.append(Command(["pi", "update", "--self"]))
    else:
        pnpm_home = str(home / PNPM_HOME_SUBPATH)
        commands.append(
            Command(["pi", "update", "--self"], {"PNPM_HOME": pnpm_home}, pnpm_home)
        )
    return commands


def upgrade_clis(commands, environ, run=subprocess.run, which=shutil.which, emit=print):
    """Run `commands`; a tool that is not installed is skipped, a failure raises.

    Every command is attempted before anything raises, so one broken upgrade
    does not hide the other. The executable is resolved against the command's
    own PATH (with `which`), which is also what finds `npm.cmd` on Windows.
    """
    missing = []
    failed = []
    for command in commands:
        env = {**environ, **command.env}
        if command.prepend_path:
            env["PATH"] = command.prepend_path + os.pathsep + environ.get("PATH", "")
        exe = which(command.argv[0], path=env.get("PATH"))
        if exe is None:
            missing.append(command.argv[0])
            continue
        argv = [exe, *command.argv[1:]]
        emit("$ " + " ".join(argv))
        if run(argv, env=env, check=False).returncode != 0:
            failed.append(" ".join(command.argv))

    if failed:
        raise RuntimeError("failed: " + "; ".join(failed))
    if missing:
        return Outcome("partial", "not installed, skipped: " + ", ".join(missing))
    return Outcome("ok")


def run_groups(groups, runners, emit=print):
    """Run each named group's runner; return every group's Outcome.

    A runner returns an Outcome (or nothing, meaning ok) and raises to fail. A
    failure never stops the run, but `stow` is skipped when `pull` blocks it or
    fails, since restowing a stale checkout links stale files.
    """
    results = {}
    blocked_by = None
    for group in groups:
        emit(f"\n== {group} ==")
        if group == "stow" and blocked_by is not None:
            results[group] = Outcome("skipped", f"dotfiles was not pulled ({blocked_by})")
            continue
        try:
            outcome = runners[group]() or Outcome("ok")
        except Exception as exc:  # pylint: disable=broad-exception-caught
            detail = getattr(exc, "message", None) or str(exc) or type(exc).__name__
            outcome = Outcome("FAILED", detail, blocks=True)
        results[group] = outcome
        if group == "pull" and outcome.blocks:
            blocked_by = outcome.detail
    return results


def any_failed(results):
    """True when any group FAILED, so the task can exit non-zero."""
    return any(o.status == "FAILED" for o in results.values())


def version(command):
    """First line of `<command> --version`, or "n/a" when absent or silent."""
    exe = shutil.which(command)
    if exe is None:
        return "n/a"
    done = subprocess.run([exe, "--version"], check=False, capture_output=True, text=True)
    lines = (done.stdout or done.stderr).strip().splitlines()
    return lines[0] if lines else "n/a"


def format_summary(results, before, after):
    """The closing report: one line per group, then each tool's version."""
    lines = ["", "== summary =="]
    for group, outcome in results.items():
        detail = f"  {outcome.detail}" if outcome.detail else ""
        lines.append(f"{group:<8} {outcome.status}{detail}")
    for tool, now in after.items():
        was = before.get(tool)
        changed = f"  (was {was})" if was != now else ""
        lines.append(f"{tool:<8} {now}{changed}")
    return "\n".join(lines)


def is_linked_worktree(path):
    """True when `path` is a linked git worktree rather than a main checkout.

    Stowing from a linked worktree points the home-directory symlinks into it,
    and they dangle once it is removed, so the stow group refuses to run there.
    """
    git_dir = _git(path, "rev-parse", "--path-format=absolute", "--git-dir").stdout.strip()
    common = _git(path, "rev-parse", "--path-format=absolute", "--git-common-dir").stdout.strip()
    return git_dir != common
