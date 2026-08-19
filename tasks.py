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
from ruamel.yaml import YAML

import instructions

# disable the check for unused-arguments to ignore unused ctx parameter in tasks
# pylint: disable=unused-argument

IS_WINDOWS = os.name == "nt"
IS_CI = os.environ.get("GITHUB_ACTIONS") == "true"
IS_ADMIN = False
EXCLUDE_DIRS = {".venv", ".git", "__pycache__", ".cache", "node_modules"}
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
    os.chdir("ansible")
    ctx.run("ansible-playbook site.yml --inventory localhost, " + shlex.join(shlex.split(args)))


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
    # Selects claude-code/.claude/output-styles/concise.md, which this repo owns.
    settings["outputStyle"] = "Concise"
    settings.setdefault("permissions", {})
    settings["permissions"]["defaultMode"] = "bypassPermissions"
    settings["skipDangerousModePermissionPrompt"] = True
    claude_settings.write_text(json.dumps(settings, indent=2) + "\n")
    print(f"Updated {claude_settings}")


def _setup_claude_mcp():
    claude_json = pathlib.Path.home() / ".claude.json"
    if not claude_json.exists():
        return
    config = json.loads(claude_json.read_text())
    config.setdefault("mcpServers", {})

    manifest = _load_plugins_manifest()
    added = []
    for name, cfg in manifest.items():
        if "mcp" not in cfg or name in config["mcpServers"]:
            continue
        config["mcpServers"][name] = cfg["mcp"]
        added.append(name)

    if added:
        claude_json.write_text(json.dumps(config, indent=2) + "\n")
        print(f"Added MCP servers to {claude_json}: {', '.join(added)}")
        print("Run /mcp in Claude Code to complete OAuth authorization for new servers.")


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

    os.chdir("ansible")

    become_arg = "" if is_termux or is_ci else "--ask-become-pass"
    ci_args = "--skip-tags desktop-only" if is_ci else ""

    ansible_pb = "../.venv/bin/ansible-playbook"
    if not pathlib.Path(ansible_pb).exists():
        ansible_pb = "ansible-playbook"

    safe_args = shlex.join(shlex.split(args))
    ctx.run(f"{ansible_pb} site.yml --inventory localhost, {become_arg} {ci_args} {safe_args}")


@task
def claude_setup(ctx):
    """Merge this repo's Claude Code settings into ~/.claude/settings.json"""
    _setup_claude_settings()


@task
def stow_skills(ctx):
    """Stow shared skills into each tool's skills discovery path"""
    _stow_shared_skills()


@task
def claude_install_mcp(ctx):
    """Register MCP servers from manifest into ~/.claude.json (user scope)"""
    _setup_claude_mcp()


@task
def claude_install_plugins(ctx):
    """Install Claude Code plugins from manifest (requires a TTY)"""
    if IS_CI:
        return
    _install_plugins(ctx, "claude")


@task
def opencode_install_plugins(ctx):
    """Install OpenCode plugins from manifest"""
    if IS_CI:
        return
    _install_plugins(ctx, "opencode")


@task(
    claude_setup,
    stow_skills,
    claude_install_mcp,
    claude_install_plugins,
    opencode_install_plugins,
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
        # Pre-create real dirs so dploy can only fold at the leaf, not higher up.
        # ai-skills: the shared skills hub exists in both this repo and
        # dotfiles_local, so two independent dploy runs write into
        # ~/.config/ai-skills. Left alone, folding happens at ~/.config and the
        # second repo to stow writes dangling links into the first repo's working
        # tree. See docs/adr/0001-pre-create-the-shared-skills-hub.md
        # pi: pi writes runtime state (npm package payloads, per-project
        # trust.json decisions with real local paths and project names, session
        # history) into ~/.pi/agent/ during normal use. Left alone, ~/.pi did not
        # previously exist, so stowing folds the whole directory into a single
        # symlink into this repo, and that runtime state lands inside the working
        # tree of a repo that is public on GitHub.
        for d in (
            self.home / ".config/ai-skills",
            self.home / ".config/ai-skills/skills",
            self.home / ".pi",
            self.home / ".pi/agent",
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
    except (OSError, DployError) as e:
        if IS_WINDOWS:
            print(f"Skipping stow on Windows: {e}")
        else:
            raise
    _stow_shared_skills()


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
_YAML = YAML()
_SHARED_SKILLS_DIR = pathlib.Path.home() / ".config" / "ai-skills" / "skills"


def _stow_shared_skills():
    """Stow shared skills from ~/.config/ai-skills/ into each tool's discovery path."""
    import dploy  # pylint: disable=C

    if not _SHARED_SKILLS_DIR.exists():
        return

    targets = [
        pathlib.Path.home() / ".claude",
        pathlib.Path.home() / ".config" / "opencode",
    ]

    src = _SHARED_SKILLS_DIR.parent  # ~/.config/ai-skills/
    for target_dir in targets:
        target_dir.mkdir(parents=True, exist_ok=True)
        _prune_dead_symlinks(target_dir / "skills")
        dploy.stow([src], target_dir, is_silent=False, ignore_patterns=["*.yaml"])


def _prune_dead_symlinks(path):
    """Remove broken symlinks at path or directly inside it (e.g. links left
    behind after the shared skills hub moved).

    Deliberately separate from Dploy.clean, despite the surface similarity.
    This is a precondition for the stow call that follows it: dploy cannot stow
    into a destination that is itself a dangling symlink, so the prune has to
    run immediately before that specific call, and it also runs from the
    stow_skills task where no Dploy sweep happens. Dploy.clean is a periodic
    sweep of $HOME limited to links pointing into the dotfiles repo, so it
    would not touch these links regardless.
    """
    if path.is_symlink() and not path.exists():
        path.unlink()
        return
    if path.is_dir():
        for entry in path.iterdir():
            if entry.is_symlink() and not entry.exists():
                entry.unlink()


def _run_cmd(ctx, cmd):
    """Run a shell command with standard echo/warn/pty settings."""
    ctx.run(cmd, echo=True, warn=True, pty=_USE_PTY)


def _run_cmds(ctx, cmds):
    """Run one or more commands (string or list of strings)."""
    if isinstance(cmds, str):
        _run_cmd(ctx, cmds)
    else:
        for cmd in cmds:
            _run_cmd(ctx, cmd)


def _load_plugins_manifest():
    """Load and merge base and local plugin manifests.

    Reads ~/.config/ai-skills/plugins.yaml (base) and ~/.config/ai-skills/plugins_local.yaml
    (local overrides), merging them together.
    """
    agents_dir = pathlib.Path.home() / ".config" / "ai-skills"
    base_path = agents_dir / "plugins.yaml"
    local_path = agents_dir / "plugins_local.yaml"

    base = {}
    if base_path.exists():
        base = _YAML.load(base_path) or {}

    local = {}
    if local_path.exists():
        local = _YAML.load(local_path) or {}

    # Merge local plugins into base (local additions win on conflict)
    return {**base, **local}


def _default_install_cmds(plugin_cfg, tool):
    """Derive default install commands from repo + plugin fields."""
    repo = plugin_cfg["repo"]
    plugin = plugin_cfg["plugin"]
    if tool == "claude":
        return [
            f"claude plugin marketplace add {shlex.quote(repo)}",
            f"claude plugin install {shlex.quote(plugin)}",
        ]
    if tool == "opencode":
        return f"npx --yes skills add {shlex.quote(repo)} --agent opencode --global --yes"
    return None


def _default_update_cmds(plugin_cfg, tool):
    """Derive default update commands from repo + plugin fields."""
    repo = plugin_cfg["repo"]
    plugin = plugin_cfg["plugin"]
    # marketplace name is the part after @ in plugin spec (e.g. "foo@bar" -> "bar")
    marketplace = plugin.split("@")[-1] if "@" in plugin else repo.split("/")[-1]
    if tool == "claude":
        return [
            f"claude plugin marketplace update {shlex.quote(marketplace)}",
            f"claude plugin update {shlex.quote(plugin)}",
        ]
    if tool == "opencode":
        return "npx --yes skills update --global"
    return None


def _install_plugins(ctx, tool):
    """Install plugins for a given tool ('claude' or 'opencode')."""
    manifest = _load_plugins_manifest()

    for _name, cfg in manifest.items():
        if "install" in cfg and tool in cfg["install"]:
            _run_cmds(ctx, cfg["install"][tool])
        elif "repo" in cfg and "plugin" in cfg:
            cmds = _default_install_cmds(cfg, tool)
            if cmds:
                _run_cmds(ctx, cmds)


def _update_plugins(ctx, tool):
    """Update plugins for a given tool ('claude' or 'opencode')."""
    manifest = _load_plugins_manifest()

    for _name, cfg in manifest.items():
        if "update" in cfg and tool in cfg["update"]:
            _run_cmds(ctx, cfg["update"][tool])
        elif "repo" in cfg and "plugin" in cfg:
            cmds = _default_update_cmds(cfg, tool)
            if cmds:
                _run_cmds(ctx, cmds)
        elif "install" in cfg and tool in cfg["install"]:
            # Fallback: re-run install commands
            _run_cmds(ctx, cfg["install"][tool])


@task
def claude_update_plugins(ctx):
    """Update installed Claude Code plugins to latest versions (requires a TTY)"""
    _update_plugins(ctx, "claude")


@task
def opencode_update_plugins(ctx):
    """Update OpenCode plugins to latest versions"""
    _update_plugins(ctx, "opencode")


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
