"""
Project Tasks that can be invoked using using the program "invoke" or "inv"
"""

import ctypes
import os
import pathlib
import shutil

from invoke import task

# disable the check for unused-arguments to ignore unused ctx parameter in tasks
# pylint: disable=unused-argument

IS_WINDOWS = os.name == "nt"
if IS_WINDOWS:
    STOW_LOCATION = "USERPROFILE"
    IS_ADMIN = ctypes.windll.shell32.IsUserAnAdmin() != 0
else:
    STOW_LOCATION = "HOME"

# try to cd to the root of the git directory because all of the tasks expect
# to be called from there.
try:
    import git
except ImportError:
    pass
else:
    try:
        GIT_REPO = git.Repo(os.getcwd(), search_parent_directories=True)
        GIT_ROOT = GIT_REPO.git.rev_parse("--show-toplevel")
        os.chdir(GIT_ROOT)
    except git.GitCommandError:
        pass


@task
def lint_shell(ctx):
    """
    Run ShellCheck on shell files
    """
    files = [str(f) for f in pathlib.Path(".").rglob("*.sh")]
    files_string = " ".join(files)

    cmd = "shellcheck --format gcc {files}"
    ctx.run(cmd.format(files=files_string))


@task
def lint_yaml(ctx):
    """
    Run yamllint on YAML Ansible configuration files
    """
    files = [str(f) for f in pathlib.Path(".").rglob("*.yml")]
    files_string = " ".join(files)

    cmd = "yamllint --format parsable {files}"
    ctx.run(cmd.format(files=files_string))


@task
def lint_python(ctx):
    """
    Run pylint and ruff on python files
    """
    exclude_dirs = {".venv", ".git", "__pycache__", ".cache"}
    files = [
        str(f)
        for f in pathlib.Path(".").rglob("*.py")
        if not any(excluded in f.parts for excluded in exclude_dirs)
    ]
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
    ctx.run("ansible-playbook site.yml --inventory localhost, " + args)


@task
def provision_termux(ctx):
    """
    Bootstrap Termux environment for Ansible and Python dependencies
    """
    bootstrap_packages = [
        "python",
        "rust",
        "build-essential",
        "git",
    ]
    ctx.run("pkg update -y")
    ctx.run(f"pkg install -y {' '.join(bootstrap_packages)}")

    # Install selene for linting
    ctx.run("cargo install selene", warn=True)

    # Sync dependencies via uv (including ansible and ruff)
    ctx.run("uv sync")


@task
def provision(ctx, args=""):
    """
    Provision this system using ansible
    """
    is_ci = os.environ.get("GITHUB_ACTIONS") == "true"
    if IS_WINDOWS:
        if IS_ADMIN:
            gui_packages = [
                "vcxsrv",
                "anki",
                "wezterm",
            ]
            common_packages = [
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
                "openssh --pre",
                "stylua",
                "selene",
            ]
            packages_to_install = common_packages
            if not is_ci:
                packages_to_install.extend(gui_packages)

            packages = " ".join(packages_to_install)
            ctx.run("choco feature enable -n=allowGlobalConfirmation")
            ctx.run(f"choco install {packages}")
            ctx.run(f"choco upgrade {packages}")
            # Enable corepack for pnpm and yarn
            ctx.run("corepack enable", warn=True)
        else:
            assert False, "You need to be admin to install things with Chocolaty"
    else:
        is_termux = "com.termux" in os.environ.get("PREFIX", "")
        if is_termux:
            provision_termux(ctx)

        # cd into ansible directory to run the playbook
        os.chdir("ansible")

        # Determine if we should use become (don't use it on Termux)
        become_arg = "" if is_termux else "--ask-become-pass"

        # Skip GUI packages in CI
        ci_args = "--skip-tags gui" if is_ci else ""

        # Determine ansible-playbook path (use venv if available)
        ansible_pb = "../.venv/bin/ansible-playbook"
        if not pathlib.Path(ansible_pb).exists():
            ansible_pb = "ansible-playbook"

        ctx.run(
            f"{ansible_pb} site.yml --inventory localhost, {become_arg} {ci_args} {args}"
        )


@task
def clean(ctx):
    """
    Clean repository using git
    """
    ctx.run("git clean --interactive")


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
        self.packages = [
            "ctags",
            "git",
            "readline",
            "scripts",
            "shell",
            "ssh",
            "tmux",
            "nvim",
            "wezterm",
            "zsh",
            "xfce4-terminal",
        ]

        if IS_WINDOWS:
            self.packages.extend(["vcxsrv", "powershell", "windows-terminal"])

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
            ]

    def stow(self):
        """
        stow and link the specified files
        """
        # pylint: disable=invalid-name
        print(self.packages)
        self.dploy.stow(self.packages, self.home, is_silent=False)
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

        self.dploy.unstow(self.packages, self.home, is_silent=False)


@task
def stow(ctx):
    """
    Run dploy stow to link all files into their respective repositories
    """
    # pylint: disable=unused-argument
    try:
        Dploy().stow()
    except OSError as e:
        if IS_WINDOWS:
            print(f"Skipping stow on Windows due to missing symlink permissions: {e}")
        else:
            raise


@task
def unstow(ctx):
    """
    Run dploy unstow to unlink all files from their respective repositories
    """
    # pylint: disable=unused-argument
    try:
        Dploy().unstow()
    except OSError as e:
        if IS_WINDOWS:
            print(f"Skipping unstow on Windows due to missing symlink permissions: {e}")
        else:
            raise


@task(provision, stow)
def install(ctx):
    """
    Install task
    """
    # pylint: disable=unused-argument


@task
def lint_lua(ctx):
    """
    Run luacheck and stylua on Lua files
    """
    exclude_dirs = {".git", ".cache", "node_modules"}
    files = [
        str(f)
        for f in pathlib.Path(".").rglob("*.lua")
        if not any(excluded in f.parts for excluded in exclude_dirs)
    ]
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
    ctx.run("ansible-playbook --syntax-check -i localhost, ansible/site.yml")


@task(lint_shell, lint_yaml, lint_python, lint_lua, lint_ansible, default=True)
def lint(ctx):
    """
    Lint task
    """
    # pylint: disable=unused-argument
