"""
Project Tasks that can be invoked using using the program "invoke" or "inv"
"""

import ctypes
import json
import os
import pathlib
import shlex
import shutil
import subprocess

from invoke import task

from manage import instructions, plugins, skills_hub

# disable the check for unused-arguments to ignore unused ctx parameter in tasks
# pylint: disable=unused-argument

IS_WINDOWS = os.name == "nt"
IS_CI = os.environ.get("GITHUB_ACTIONS") == "true"
IS_ADMIN = False
EXCLUDE_DIRS = {".venv", ".git", "__pycache__", ".cache", "node_modules"}
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


@task
def lint_shell(ctx):
    """
    Run ShellCheck on shell files
    """
    files_string = " ".join(_find_files("*.sh"))
    ctx.run(f"shellcheck --format gcc {files_string}")


@task
def lint_yaml(ctx):
    """
    Run yamllint on YAML Ansible configuration files
    """
    files_string = " ".join(_find_files("*.yml"))
    ctx.run(f"yamllint --format parsable {files_string}")


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
    bootstrap_system_packages = [
        "python",
        "rust",
        "build-essential",
        "git",
    ]
    ctx.run("pkg update -y")
    ctx.run(f"pkg install -y {' '.join(bootstrap_system_packages)}")

    # Install selene for linting
    ctx.run("cargo install selene", warn=True)

    # Sync dependencies via uv (excluding dev dependencies like ruff)
    ctx.run("uv sync --no-dev")


def _setup_gitconfig_local():
    gitconfig_local = pathlib.Path.home() / ".gitconfig_local"
    if not gitconfig_local.exists():
        gitconfig_local.write_text("[include]\n    path = ~/.gitconfig_personal\n")
        print(f"Created {gitconfig_local}")


def _setup_claude_settings():
    claude_settings = pathlib.Path.home() / ".claude" / "settings.json"
    if not claude_settings.exists():
        return
    settings = json.loads(claude_settings.read_text())
    settings["voiceEnabled"] = True
    # Selects claude-code/.claude/output-styles/concise.md, generated from the
    # prose-style fragment. Deleting the key here would leave Claude's own
    # brevity instructions in force, which the fragment is meant to replace.
    settings["outputStyle"] = "Concise"
    settings.setdefault("permissions", {})
    settings["permissions"]["defaultMode"] = "bypassPermissions"
    settings["skipDangerousModePermissionPrompt"] = True
    claude_settings.write_text(json.dumps(settings, indent=2) + "\n")
    print(f"Updated {claude_settings}")


def _amend_mcp_servers(config_path, servers):
    """Add manifest servers missing from a harness-owned MCP config; return names added.

    For a file the harness itself creates and writes far more than MCP config into.
    Existing entries are left untouched, so a server whose definition changed here
    has to be edited (or deleted and regenerated) in that file by hand. An absent
    file stays absent: a stub written before the harness's first run would be a
    config file it never asked for.
    """
    if not config_path.exists():
        return []

    config = json.loads(config_path.read_text())
    config.setdefault("mcpServers", {})
    added = [name for name in servers if name not in config["mcpServers"]]
    if not added:
        return []

    for name in added:
        config["mcpServers"][name] = servers[name]
    config_path.write_text(json.dumps(config, indent=2) + "\n")
    return added


def _write_mcp_config(config_path, servers):
    """Generate a whole MCP config file from the manifest; return True if it changed.

    Unlike _amend_mcp_servers this owns the file outright, so an edited or removed
    manifest entry propagates. Only use it for a path no harness writes to itself,
    or the harness's own writes get discarded on the next provisioning run.
    """
    content = json.dumps({"mcpServers": servers}, indent=2) + "\n"
    if config_path.exists() and config_path.read_text() == content:
        return False

    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(content)
    return True


def _setup_mcp_servers():
    """Register manifest MCP servers with every harness that reads an MCP config file.

    One manifest entry per server feeds both harnesses, so neither drifts from the
    declaration. The two are written differently because the files differ in
    ownership: Claude Code creates ~/.claude.json and keeps its whole state there,
    while ~/.agents/mcp.json is one of the global paths pi-mcp-adapter merges and
    the only one it never writes to itself (its /mcp panel writes
    ~/.pi/agent/mcp.json, which is left free for exactly that).
    """
    servers = plugins.load().mcp_servers()
    if not servers:
        return

    home = pathlib.Path.home()
    claude_json = home / ".claude.json"
    added = _amend_mcp_servers(claude_json, servers)
    if added:
        print(f"Added MCP servers to {claude_json}: {', '.join(added)}")
        print("Run /mcp in Claude Code to authorize any of them that use OAuth.")

    pi_config = home / ".agents" / "mcp.json"
    if _write_mcp_config(pi_config, servers):
        print(f"Wrote {len(servers)} MCP servers to {pi_config}")


def _setup_pi_settings():
    """Write the manifest's pi packages into pi's own settings file.

    Mixed ownership, which is why neither MCP helper fits: `packages` belongs to
    the manifest, so dropping a declaration there drops the package here, while
    every other key is pi's own -- theme, provider and model defaults, changelog
    state -- and survives untouched. Declaring in the manifest rather than in a
    stowed settings.json is what lets plugins_local.yaml add a private package,
    and keeps machine-local preferences out of this public repo.

    Unlike _amend_mcp_servers an absent file is created rather than left alone:
    this file is what `pi update --extensions` reconciles against, so skipping it
    on a machine that has never run pi would mean no package is ever installed.
    """
    packages = plugins.load().pi_packages()
    if not packages:
        return

    settings_path = pathlib.Path.home() / ".pi" / "agent" / "settings.json"
    # A machine that stowed the settings.json this repo used to commit still has
    # a symlink to a path the repo no longer has. Writing through it would
    # recreate the file inside the working tree, which is what moving the
    # declaration here removes. inv clean-stow prunes the dead link eventually;
    # this must not depend on that having run first.
    if settings_path.is_symlink():
        settings_path.unlink()

    settings = json.loads(settings_path.read_text()) if settings_path.exists() else {}
    settings["packages"] = packages
    settings["enableSkillCommands"] = True
    settings["quietStartup"] = True

    content = json.dumps(settings, indent=2) + "\n"
    if settings_path.exists() and settings_path.read_text() == content:
        return

    settings_path.parent.mkdir(parents=True, exist_ok=True)
    settings_path.write_text(content)
    print(f"Declared {len(packages)} pi packages in {settings_path}")


def _provision_windows(ctx, is_ci: bool) -> None:
    if not IS_ADMIN:
        raise SystemExit("You need to be admin to install things with Chocolatey")

    gui_system_packages = [
        "nerd-fonts-dejavusansmono",
        "vcxsrv",
        "anki",
        "wezterm",
    ]
    common_system_packages = [
        "llvm",
        "pandoc",
        "git",
        "ctags",
        "neovim",
        "nodejs",
        "plantuml",
        "fzf",
        "zoxide",
        "eza",
        "bat",
        "delta",
        "gsudo",
        "ripgrep",
        "oh-my-posh",
        "poshgit",
        "stylua",
        "selene",
        "claude-code",
        "opencode",
    ]
    system_packages_to_install = common_system_packages
    if not is_ci:
        system_packages_to_install.extend(gui_system_packages)

    system_packages = " ".join(system_packages_to_install)
    ctx.run(f"choco install -y {system_packages}", pty=False)
    ctx.run("choco install -y openssh --pre", pty=False)
    ctx.run(f"choco upgrade -y {system_packages}", pty=False)
    ctx.run("choco upgrade -y openssh --pre", pty=False)
    ctx.run("corepack enable", warn=True, pty=False)


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
    _setup_claude_settings()


@task
def stow_skills(ctx):
    """Stow shared skills into each tool's skills discovery path"""
    skills_hub.stow_out()


@task
def install_mcp(ctx):
    """Register MCP servers from the manifest for Claude Code and pi"""
    _setup_mcp_servers()


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
    _setup_pi_settings()


@task
def pi_install_plugins(ctx):
    """Reconcile pi packages declared in the manifest"""
    if IS_CI:
        return
    _run_cmd(ctx, "pi update --extensions")


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


class Dploy:
    """
    Class to handle logic and data to stow and unstow using dploy
    """

    def __init__(self):
        # do a file level import so this whole script isn't dependant on dploy
        # preventing us from installing it using the provision task
        import dploy  # pylint: disable=C

        self.dploy = dploy
        self.home = pathlib.Path().home()
        self.stow_packages = [
            "agents",
            "claude-code",
            "ctags",
            "git",
            "neovide",
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

        if IS_WINDOWS:
            self.stow_packages.extend(["powershell", "vcxsrv"])

        # pylint: disable=invalid-name
        p = pathlib.Path

        self.links = []

        dropbox = self.home / p("Dropbox")
        files = self.home / p("files")
        if dropbox.exists():
            self.links.append((dropbox, files))
        else:

            def mkdir(path):
                path.mkdir(parents=True, exist_ok=True)
                print(f"Creating Directory {path}")

            mkdir(files / p("documents") / p("archive"))
            mkdir(files / p("projects") / p("archive"))
            mkdir(files / p("notes") / p("archive"))

        if IS_WINDOWS:
            self.links += [
                (self.home / p(".config/nvim"), self.home / p("AppData/Local/nvim")),
                (
                    self.home / p(".config/neovide"),
                    self.home / p("AppData/Roaming/neovide"),
                ),
            ]

    def stow(self):
        """
        stow and link the specified files
        """
        # pylint: disable=invalid-name
        print(self.stow_packages)
        # The hub's own pre-create, and the rationale for it, live with the hub.
        skills_hub.pre_create(self.home)
        # Pre-create real dirs so dploy can only fold at the leaf, not higher up.
        # pi: pi writes runtime state (npm package payloads, per-project
        # trust.json decisions with real local paths and project names, session
        # history) into ~/.pi/agent/ during normal use. Left alone, ~/.pi did not
        # previously exist, so stowing folds the whole directory into a single
        # symlink into this repo, and that runtime state lands inside the working
        # tree of a repo that is public on GitHub.
        # ai-instructions: a dotfiles_local repo drops a private local.md beside
        # these fragments, and the generated instruction files tell every agent to
        # read it. Folding would make that private file land in this public repo.
        for d in (
            self.home / ".pi",
            self.home / ".pi/agent",
            self.home / ".config/ai-instructions",
        ):
            d.mkdir(parents=True, exist_ok=True)
        self.dploy.stow(self.stow_packages, self.home, is_silent=False)
        for src, dest in self.links:
            self.dploy.link(src, dest, is_silent=False)

    def unstow(self):
        """
        unstow and link the specified files
        """
        for _, dest in reversed(self.links):
            try:
                os.unlink(dest)
            except FileNotFoundError:
                pass

        self.dploy.unstow(self.stow_packages, self.home, is_silent=False)

    def clean(self):
        """
        remove dead symlinks left over from stowing

        Replaces dploy's own clean sub-command, which traverses the entire stow
        destination and chokes on permission-denied entries along the way (a
        frequent failure on Windows). This walk is depth-limited to the deepest
        package path, skips EXCLUDE_DIRS, and swallows PermissionError.
        """
        repo_dir = pathlib.Path(__file__).resolve().parent
        max_depth = max(
            len(p.relative_to(pkg).parts)
            for pkg in self.stow_packages
            for p in pathlib.Path(pkg).rglob("*")
        )
        self._clean_dead_links(self.home, repo_dir, max_depth)

    def _clean_dead_links(self, directory, repo_dir, max_depth, current_depth=0):
        """
        Recursively find and remove dead symlinks that point into the dotfiles
        repo, limited by depth and skipping permission-denied directories.
        """
        if current_depth > max_depth:
            return

        try:
            entries = list(directory.iterdir())
        except PermissionError:
            return

        for entry in entries:
            if entry.is_symlink():
                target = (entry.parent / entry.readlink()).resolve()
                if not target.exists() and repo_dir in target.parents:
                    print(f"removing dead link: {entry}")
                    entry.unlink()
            elif entry.is_dir() and not entry.is_symlink():
                if entry.name in EXCLUDE_DIRS:
                    continue
                self._clean_dead_links(entry, repo_dir, max_depth, current_depth + 1)


@task
def stow(ctx):
    """
    Run dploy stow to link all files into their respective repositories
    """
    # pylint: disable=unused-argument,import-outside-toplevel
    from dploy.error import DployError

    try:
        d = Dploy()
        d.clean()
        d.stow()
        skills_hub.stow_out(d.home)
    except (OSError, DployError) as e:
        if IS_WINDOWS:
            print(f"Skipping stow: {e}")
        else:
            raise


@task
def unstow(ctx):
    """
    Run dploy unstow to unlink all files from their respective repositories
    """
    # pylint: disable=unused-argument,import-outside-toplevel
    from dploy.error import DployError

    try:
        Dploy().unstow()
    except (OSError, DployError) as e:
        if IS_WINDOWS:
            print(f"Skipping unstow on Windows: {e}")
        else:
            raise


@task
def clean_stow(ctx):
    """
    Remove dead symlinks left over from stowing
    """
    # pylint: disable=unused-argument,import-outside-toplevel
    from dploy.error import DployError

    try:
        Dploy().clean()
    except (OSError, DployError) as e:
        if IS_WINDOWS:
            print(f"Skipping clean on Windows: {e}")
        else:
            raise


_USE_PTY = not IS_WINDOWS
def _run_cmd(ctx, cmd):
    """Run a shell command with standard echo/warn/pty settings."""
    ctx.run(cmd, echo=True, warn=True, pty=_USE_PTY)


def _run_plugin_cmds(ctx, tool, action):
    """Run every manifest command for a tool and an action ("install"/"update")."""
    for cmd in plugins.load().commands(tool, action):
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

    # Use stylua to check formatting
    if shutil.which("stylua"):
        ctx.run(f"stylua --check {files_string}")
    else:
        print("stylua not found, skipping...")

    # Use selene for linting
    if shutil.which("selene"):
        ctx.run(f"selene {files_string}")
    else:
        print("selene not found, skipping...")


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
    drift = instructions.generate(check=check)
    if drift:
        paths = "\n  ".join(drift)
        raise SystemExit(
            "Generated instruction files are out of date:\n  "
            f"{paths}\n"
            "Run `uv run inv gen-instructions` and commit the result."
        )


@task
def lint_instructions(ctx):
    """
    Check generated instruction files match their fragments
    """
    gen_instructions(ctx, check=True)


@task
def test(ctx):
    """
    Run the Python test suite
    """
    ctx.run("pytest -q")


@task(
    lint_shell,
    lint_yaml,
    lint_python,
    lint_lua,
    lint_ansible,
    lint_instructions,
    default=True,
)
def lint(ctx):
    """
    Lint task
    """
    # pylint: disable=unused-argument
