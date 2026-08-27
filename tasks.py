"""
Project Tasks that can be invoked using using the program "invoke" or "inv"
"""

import ctypes
import os
import pathlib
import shlex
import shutil
import subprocess
import sys

from invoke import task

from manage import agents
from manage import provision as provision_data
from manage.repo import EXCLUDE_DIRS, IS_WINDOWS
from manage.stow import StowPlan, tolerating_windows_symlink_failure

# disable the check for unused-arguments to ignore unused ctx parameter in tasks
# pylint: disable=unused-argument

IS_CI = os.environ.get("GITHUB_ACTIONS") == "true"
IS_ADMIN = False
# Ansible resolves ansible.cfg from the working directory, so the playbook runs
# from here. Entered per command with ctx.cd rather than os.chdir: invoke runs
# pre-tasks in one process, so a chdir that outlives its command leaves every
# task composed after it resolving relative paths from the wrong root.
ANSIBLE_DIR = "ansible"
if IS_WINDOWS:
    STOW_LOCATION = "USERPROFILE"
    IS_ADMIN = ctypes.windll.shell32.IsUserAnAdmin() != 0
else:
    STOW_LOCATION = "HOME"

# try to cd to the root of the git directory because all of the tasks expect
# to be called from there.
try:
    GIT_ROOT = subprocess.check_output(
        ["git", "rev-parse", "--show-toplevel"],
        stderr=subprocess.DEVNULL,
        text=True
    ).strip()
    os.chdir(GIT_ROOT)
except (subprocess.CalledProcessError, FileNotFoundError):
    pass


def _find_files(pattern: str) -> list[str]:
    return [
        f.as_posix()
        for f in pathlib.Path(".").rglob(pattern)
        if not EXCLUDE_DIRS & set(f.parts)
    ]


# Missing-linter policy, applied by every lint task through _run_linter:
# a linter whose binary is absent is a hard error in CI and a loud skip
# locally. CI installs the tools deliberately, so an absent one there means
# the install broke and a green run would be green for the wrong reason.
# Locally a developer may not have every tool, so the run continues -- but
# each skip is announced and the set of skips is repeated at the end of the
# lint run, so a clean run cannot be mistaken for a complete one.
#
# Two things this policy is not about. A linter that does not apply to the
# platform at all (shellcheck on Windows, ansible-playbook on Windows) is
# scoped out by its task and never reaches here. Linters run as `python -m`
# (pylint, ruff) are declared dependencies of this repo's own environment,
# so their absence is a broken `uv sync`, not a missing system package.
SKIPPED_LINTERS: list[str] = []


def _run_linter(ctx, tool: str, command: str) -> None:
    """
    Run `command` if `tool` is on PATH.

    Raises SystemExit when the tool is missing under CI; otherwise records the
    skip in SKIPPED_LINTERS and returns. See the missing-linter policy above.
    """
    if shutil.which(tool):
        ctx.run(command)
        return
    if IS_CI:
        raise SystemExit(
            f"{tool} not found on PATH. CI installs every linter, so this is an "
            "install failure, not an optional tool -- fix the install step "
            "rather than skipping the check."
        )
    print(f"{tool} not found, skipping...")
    SKIPPED_LINTERS.append(tool)


@task
def lint_shell(ctx):
    """
    Run ShellCheck on shell files
    """
    # The shell scripts here target Linux and Termux; nothing runs them on
    # Windows, and the Linux job already lints the same files.
    if IS_WINDOWS:
        print("shell scripts are not a Windows target, skipping...")
        return
    files_string = " ".join(_find_files("*.sh"))
    _run_linter(ctx, "shellcheck", f"shellcheck --format gcc {files_string}")


@task
def lint_yaml(ctx):
    """
    Run yamllint on YAML Ansible configuration files
    """
    files_string = " ".join(_find_files("*.yml"))
    _run_linter(ctx, "yamllint", f"yamllint --format parsable {files_string}")


@task
def lint_python(ctx):
    """
    Run pylint and ruff on python files
    """
    files = _find_files("*.py")
    files_string = " ".join(files)
    cmds = ["pylint --output-format=parseable", "ruff check"]
    base_cmd = "python -m {cmd} {files}"
    for cmd in cmds:
        if "ruff" in cmd:
            ctx.run(f"{cmd} {files_string}")
        else:
            ctx.run(base_cmd.format(cmd=cmd, files=files_string))


@task
def provision_all(ctx, args=""):
    """
    Provision this and other system using ansible
    """
    with ctx.cd(ANSIBLE_DIR):
        ctx.run(
            "ansible-playbook site.yml --inventory localhost, "
            + shlex.join(shlex.split(args))
        )


@task
def provision_termux(ctx):
    """
    Bootstrap Termux environment for Ansible and Python dependencies
    """
    bootstrap = provision_data.termux_bootstrap_system_packages()
    ctx.run("pkg update -y")
    ctx.run(f"pkg install -y {' '.join(bootstrap)}")

    # Install selene for linting
    ctx.run("cargo install selene", warn=True)

    # Sync dependencies via uv (excluding dev dependencies like ruff)
    ctx.run("uv sync --no-dev")


def _setup_gitconfig_local():
    gitconfig_local = pathlib.Path.home() / ".gitconfig_local"
    if not gitconfig_local.exists():
        gitconfig_local.write_text("[include]\n    path = ~/.gitconfig_personal\n")
        print(f"Created {gitconfig_local}")


def _choco_each(ctx, packages: list[str]) -> None:
    """
    Install and upgrade each Chocolatey package on its own, then report failures.

    One `choco install` for the whole list aborts every remaining package when any
    single one fails, and third-party packages fail for reasons outside this repo:
    a dead upstream download URL, a hung install script, a registry blip. Per
    package, that costs one tool instead of the entire Windows provision.

    Failures are collected and printed together at the end, because Chocolatey's
    own output is long enough to bury a single failure line. Provisioning still
    succeeds -- a machine missing one optional tool is worth having. Nothing here
    is load-bearing for `inv lint`; the pnpm chain the caller runs afterwards is,
    and it stays a hard error.
    """
    failed: list[str] = []
    for package in packages:
        # `choco install` no-ops on an already-installed package rather than
        # updating it, so the upgrade is what actually moves the version.
        install = ctx.run(f"choco install -y {package}", warn=True, pty=False)
        upgrade = ctx.run(f"choco upgrade -y {package}", warn=True, pty=False)
        if not install.ok and not upgrade.ok:
            failed.append(package)

    if failed:
        print(f"\nChocolatey packages that failed: {', '.join(failed)}")
        print(
            "Provisioning continued without them. A package that keeps failing "
            "is usually broken upstream -- check its download URL before "
            "assuming this machine is at fault."
        )


def _provision_windows(ctx, is_ci: bool) -> None:
    if not IS_ADMIN:
        raise SystemExit("You need to be admin to install things with Chocolatey")

    # A headless host (CI) has no desktop session, so the desktop-only
    # packages are left out there.
    packages = provision_data.windows_system_packages(desktop=not is_ci)
    # openssh needs --pre (no stable Chocolatey release), so it carries its own
    # flag rather than joining the plain list.
    _choco_each(ctx, packages + ["openssh --pre"])

    # Corepack is not bundled with the nodejs Chocolatey package, so it has to be
    # installed before it can be enabled -- `corepack enable` alone fails with
    # "'corepack' is not recognized". This mirrors the Linux chain in
    # ansible/tasks/javascript-packages.yml; keep the two in step.
    #
    # Only `corepack enable` tolerates failure, and only because the npm fallback
    # below covers it. The install is a hard error: without pnpm on PATH, `inv
    # lint` cannot run its TypeScript step at all.
    ctx.run("npm install -g --force corepack", pty=False)
    if not ctx.run("corepack enable", warn=True, pty=False).ok:
        ctx.run("npm install -g pnpm", pty=False)


def _provision_linux(ctx, is_ci: bool, args: str) -> None:
    is_termux = "com.termux" in os.environ.get("PREFIX", "")
    if is_termux:
        provision_termux(ctx)

    become_arg = "" if is_termux or is_ci else "--ask-become-pass"
    ci_args = "--skip-tags desktop-only" if is_ci else ""

    # Paths are relative to ANSIBLE_DIR, which the command runs in; the check is
    # relative to the repo root, which this process stays in.
    ansible_pb = "ansible-playbook"
    if (pathlib.Path(".venv") / "bin" / "ansible-playbook").exists():
        ansible_pb = "../.venv/bin/ansible-playbook"

    safe_args = shlex.join(shlex.split(args))
    with ctx.cd(ANSIBLE_DIR):
        ctx.run(
            f"{ansible_pb} site.yml --inventory localhost, "
            f"{become_arg} {ci_args} {safe_args}"
        )


@task
def claude_setup(ctx):
    """Merge this repo's Claude Code settings into ~/.claude/settings.json"""
    agents.settings.setup_claude()


@task
def stow_skills(ctx):
    """Stow shared skills into each tool's skills discovery path"""
    # Unguarded on purpose. The fan-out is the whole point of this task, so a
    # Windows privilege failure is its result, not an incidental step to skip
    # past; silently succeeding would report skills stowed that are not. The
    # `stow` task tolerates the same failure because there it is one step of
    # many.
    agents.skills_hub.stow_out()


@task
def install_mcp(ctx):
    """Register MCP servers from the manifest for Claude Code and pi"""
    agents.mcp.register()


@task
def claude_install_plugins(ctx):
    """Install Claude Code plugins from manifest (requires a TTY)"""
    if IS_CI:
        return
    _run_plugin_cmds(ctx, "claude", "install")


@task
def opencode_install_plugins(ctx):
    """Install OpenCode plugins from manifest"""
    if IS_CI:
        return
    _run_plugin_cmds(ctx, "opencode", "install")


@task
def pi_setup(ctx):
    """Declare the manifest's pi packages in ~/.pi/agent/settings.json"""
    agents.settings.setup_pi()


@task
def pi_install_plugins(ctx):
    """Reconcile pi packages declared in the manifest"""
    if IS_CI:
        return
    _run_cmd(ctx, "pi update --extensions")


def _herdr_install_integration(ctx):
    """Install herdr's agent-state integration into pi's extensions directory.

    Called from `stow`, not from `setup_ai`, because `herdr integration install`
    needs ~/.pi/agent/extensions to exist and that directory is created by
    stowing's own fold barriers. setup_ai runs as a post hook of provision, which
    is still before stow, so it is too early.

    ansible/tasks/herdr.yml attempts the same install and tolerates failing, for
    the machine whose very first provision predates any stow. Reinstalling an
    up-to-date integration is a no-op, so doing it in both places is harmless.

    `ctx` may be None: the stow task's tests call `stow.body(None)`, so this must
    stay a no-op without a runner rather than fail the task that invoked it.
    """
    if ctx is None or IS_WINDOWS or not shutil.which("herdr"):
        return
    _run_cmd(ctx, "herdr integration install pi")


@task(
    claude_setup,
    stow_skills,
    install_mcp,
    claude_install_plugins,
    opencode_install_plugins,
    pi_setup,
    pi_install_plugins,
)
def setup_ai(ctx):
    """Set up AI coding agent settings, MCP servers, skills, and plugins"""
    # pylint: disable=unused-argument


@task(post=[setup_ai])
def provision(ctx, args=""):
    """
    Provision this system using ansible
    """
    _setup_gitconfig_local()
    if IS_WINDOWS:
        _provision_windows(ctx, IS_CI)
    else:
        _provision_linux(ctx, IS_CI, args)


@task
def clean(ctx):
    """
    Clean repository using git
    """
    ctx.run("git clean --interactive", pty=True)


@task
def stow(ctx):
    """
    Run dploy stow to link all files into their respective repositories
    """
    # pylint: disable=unused-argument
    # The shared-skills fan-out is inside the guard deliberately. This is the
    # whole-machine entry point -- `inv all` and CI run it -- so a Windows
    # privilege failure anywhere in it should skip, not abort the run. `inv
    # stow-skills` asks for that fan-out alone and leaves it unguarded.
    with tolerating_windows_symlink_failure("stow"):
        d = StowPlan()
        d.clean()
        d.stow()
        agents.skills_hub.stow_out(d.home)
    # After stowing, so ~/.pi/agent/extensions exists for herdr to install into.
    _herdr_install_integration(ctx)


@task
def unstow(ctx):
    """
    Run dploy unstow to unlink all files from their respective repositories
    """
    # pylint: disable=unused-argument
    with tolerating_windows_symlink_failure("unstow"):
        StowPlan().unstow()


@task
def clean_stow(ctx):
    """
    Remove dead symlinks left over from stowing
    """
    # pylint: disable=unused-argument
    with tolerating_windows_symlink_failure("clean-stow"):
        StowPlan().clean()


_USE_PTY = not IS_WINDOWS
def _run_cmd(ctx, cmd):
    """Run a shell command with standard echo/warn/pty settings."""
    ctx.run(cmd, echo=True, warn=True, pty=_USE_PTY)


def _run_plugin_cmds(ctx, tool, action):
    """Run every manifest command for a tool and an action ("install"/"update")."""
    for cmd in agents.plugins.load().commands(tool, action):
        _run_cmd(ctx, cmd)


@task
def claude_update_plugins(ctx):
    """Update installed Claude Code plugins to latest versions (requires a TTY)"""
    _run_plugin_cmds(ctx, "claude", "update")


@task
def opencode_update_plugins(ctx):
    """Update OpenCode plugins to latest versions"""
    _run_plugin_cmds(ctx, "opencode", "update")


@task
def pi_update_plugins(ctx):
    """Update pi packages from manifest"""
    if IS_CI:
        return
    _run_plugin_cmds(ctx, "pi", "update")


@task(provision, stow, name="all")
def all_(ctx):
    """
    Provision this system and stow every stow package
    """
    # pylint: disable=unused-argument


@task
def lint_lua(ctx):
    """
    Run luacheck and stylua on Lua files
    """
    files = _find_files("*.lua")
    if not files:
        return
    files_string = " ".join(files)
    _run_linter(ctx, "stylua", f"stylua --check {files_string}")
    _run_linter(ctx, "selene", f"selene {files_string}")


@task
def lint_typescript(ctx):
    """
    Run Biome and the TypeScript compiler on TypeScript files
    """
    if not _find_files("*.ts"):
        return
    # Both tools read their config from the repo root and discover their own file
    # lists, so neither takes the file list as arguments. tsc fails outright with
    # TS18003 when it resolves no inputs, which is why the early return above is a
    # guard and not an optimisation. That guard is only sound while this find and
    # tsconfig.json's include/exclude resolve the same set across the whole repo:
    # widen one without the other and lint either dies on TS18003 or silently
    # stops type-checking a file biome still lints.
    ctx.run("pnpm exec biome check .")
    ctx.run("pnpm exec tsc --noEmit")


@task
def lint_ansible(ctx):
    """
    Run ansible-playbook syntax check on the ansible playbook
    """
    if IS_WINDOWS:
        print("ansible-playbook syntax check not supported on Windows, skipping...")
        return
    ctx.run("ansible-playbook --syntax-check -i localhost, ansible/site.yml")


@task(help={"check": "Report drift instead of writing files"})
def gen_instructions(ctx, check=False):
    """
    Generate agent instruction files from shared fragments
    """
    drift = agents.instructions.generate(check=check)
    if drift:
        paths = "\n  ".join(drift)
        raise SystemExit(
            "Generated instruction files are out of date:\n  "
            f"{paths}\n"
            "Run `uv run inv gen-instructions` and commit the result."
        )


@task
def gen_framing(ctx, check=False):
    """
    Generate the adapters' catalog framing from the resolver's constants
    """
    # pylint: disable=unused-argument
    from manage.knowledge import framing  # pylint: disable=import-outside-toplevel

    if framing.generate(check=check):
        sys.exit("Generated framing is stale -- run `uv run inv gen-framing`")


@task
def lint_framing(ctx):
    """
    Fail when the generated framing has drifted from the resolver
    """
    gen_framing(ctx, check=True)


@task
def lint_instructions(ctx):
    """
    Check generated instruction files match their fragments
    """
    gen_instructions(ctx, check=True)


@task
def test(ctx):
    """
    Run the test suites
    """
    ctx.run("pytest -q")
    test_typescript(ctx)


@task
def test_typescript(ctx):
    """
    Run the TypeScript adapter contract tests
    """
    # node's own runner and type stripping, so this needs nothing beyond the
    # toolchain lint_typescript already requires. Node 22+ for --experimental-
    # strip-types; the flag is still required in 22, silent in 24.
    files = _find_files("*.test.ts")
    if not files:
        return
    _run_linter(
        ctx,
        "node",
        f"node --experimental-strip-types --test {' '.join(files)}",
    )


@task(
    lint_shell,
    lint_yaml,
    lint_python,
    lint_lua,
    lint_typescript,
    lint_ansible,
    lint_instructions,
    lint_framing,
    default=True,
)
def lint(ctx):
    """
    Lint task
    """
    # pylint: disable=unused-argument
    # The per-linter skip messages scroll away behind the output of the
    # linters that did run, so repeat them once at the end: this is the line
    # that keeps a clean run from reading as a complete one.
    if SKIPPED_LINTERS:
        print(
            "Lint incomplete -- these linters were not installed and were "
            f"skipped: {', '.join(SKIPPED_LINTERS)}"
        )
