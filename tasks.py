"""
Project Tasks that can be invoked using using the program "invoke" or "inv"
"""

import os
import fnmatch
import pathlib
from invoke import task

# disable the check for unused-arguments to ignore unused ctx parameter in tasks
# pylint: disable=unused-argument

IS_WINDOWS = os.name == 'nt'
if IS_WINDOWS:
    # setting 'shell' is a work around for issue #345 of invoke
    RUN_ARGS = {'pty': False, 'shell': r'C:\Windows\System32\cmd.exe'}
    STOW_LOCATION = 'USERPROFILE'
else:
    RUN_ARGS = {'pty': True}
    STOW_LOCATION = 'HOME'


# try to cd to the root of the git directory because all of the tasks expect
# to be called from there.
try:
    import git
    GIT_REPO = git.Repo(os.getcwd(), search_parent_directories=True)
    GIT_ROOT = GIT_REPO.git.rev_parse("--show-toplevel")
    os.chdir(GIT_ROOT)
except ImportError:
    pass


def find_files(directory, pattern):
    """
    Recursively find files in directory using the glob expression pattern

    The Python 3.5 glob module supports recursive globs, and the python 3.4
    pathlib module also does, but for version 2.2 to 3.3 this is the work
    around.  source: http://stackoverflow.com/a/2186673
    """
    for root, _, files in os.walk(directory):
        for basename in files:
            if fnmatch.fnmatch(basename, pattern):
                filename = os.path.join(root, basename)
                yield filename


@task
def lint_vim(ctx):
    """
    Run Vint vim linter on .vimrc and other supporting files
    """
    files = [
        os.path.join('vim', '.vim', 'vimrc'),
        os.path.join('vim', '.vim', 'autoload', '*.vim'),
    ]
    files_string = " ".join(files)

    cmd = 'vint {files}'
    ctx.run(cmd.format(files=files_string), **RUN_ARGS)


@task
def lint_shell(ctx):
    """
    Run ShellCheck on shell files
    """

    files = [
        os.path.join('git', 'bin', '*'),
        os.path.join('scripts', 'bin', '*.sh'),
        os.path.join('scripts', 'bin', 'trash'),
    ]
    files_string = ' '.join(files)

    cmd = 'shellcheck --format gcc {files}'
    ctx.run(cmd.format(files=files_string), **RUN_ARGS)


@task
def lint_yaml(ctx):
    """
    Run yamllint on YAML Ansible configuration files
    """
    files = [os.path.join('ansible', '*.yml')]
    files.extend(find_files(directory='ansible/roles', pattern='*.yml'))
    files_string = " ".join(files)

    cmd = 'yamllint --format parsable {files}'
    ctx.run(cmd.format(files=files_string), **RUN_ARGS)


@task
def lint_python(ctx):
    """
    Run pylint on this file
    """
    files = [
        'tasks.py',
    ]

    cmds = ['pylint --output-format=parseable', 'flake8']
    files_string = ' '.join(files)
    base_cmd = 'python3 -m {cmd} {files}'

    for cmd in cmds:
        ctx.run(base_cmd.format(cmd=cmd, files=files_string),
                **RUN_ARGS)


@task
def provision_all(ctx, args=''):
    """
    Provision this and other system using ansible
    """
    os.chdir('ansible')
    ctx.run('ansible-playbook site.yml --ask-vault-pass --inventory hosts' + ' ' + args,
            **RUN_ARGS)


@task
def provision(ctx, args=''):
    """
    Provision this system using ansible
    """
    if IS_WINDOWS:
        packages = " ".join([
            "git",
            "ctags",
            "neovim",
            "nodejs",
            "plantuml",
            "openssh -params '\"/SSHServerFeature\"' -y",
            "windows-terminal --pre",
            "unison",
            "terminus",
            "vcxsrv",  # X-Serve
            "wsl-ubuntu-1804",
        ])
        ctx.run(f'choco install {packages} -y', **RUN_ARGS)
        ctx.run('choco update all -y', **RUN_ARGS)
    else:
        os.chdir('ansible')
        ctx.run('ansible-playbook site.yml --ask-vault-pass --inventory localhost '
                '--ask-become-pass ' + args,
                **RUN_ARGS)


@task
def provision_minimal(ctx, args=''):
    """
    Provision this system using ansible
    """
    os.chdir('ansible')
    ctx.run('ansible-playbook site-minimal.yml --ask-vault-pass --inventory localhost '
            '--ask-become-pass ' + args,
            **RUN_ARGS)


@task
def clean(ctx):
    """
    Clean repository using git
    """
    ctx.run('git clean --interactive', **RUN_ARGS)


@task
def requirements(ctx, args=''):
    """
    Install python requirements
    """
    ctx.run('pip install ' + args + ' --requirement requirements.txt', **RUN_ARGS)


class Dploy():
    """
    Class to handle logic and data to stow and unstow using dploy
    """
    def __init__(self):
        # do a file level import so this whole script isn't dependant on dploy
        # preventing us from installing it using the provision task
        import dploy
        self.dploy = dploy
        self.home = pathlib.Path().home()
        self.packages = [
            'cmd',
            'ctags',
            'git',
            'readline',
            'scripts',
            'shell',
            'ssh',
            'tmux',
            'vim',
            'zsh',
            'xfce4-terminal',
        ]

        if IS_WINDOWS:
            self.packages.extend(
                [
                    'vcxsrv',
                    'powershell',
                    'windows-terminal'
                ]
            )

        # pylint: disable=invalid-name
        p = pathlib.Path

        self.links = [
            (
                self.home / p('.vim/vimrc'),
                self.home / p('.vimrc')
            ),
            (
                self.home / p('.vim'),
                self.home / p('vimfiles')
            ),
            (
                self.home / p('.vim/vimrc'),
                self.home / p('.vim/init.vim')
            ),
            (
                self.home / p('.vim'),
                self.home / p('.config/nvim')
            ),
        ]

        dropbox = self.home / p('Dropbox')
        files = self.home / p('files')
        if dropbox.exists():
            self.links.append((dropbox, files))
        else:
            def mkdir(path):
                path.mkdir(parents=True, exist_ok=True)
                print(f"Creating Directory {path}")
            mkdir(files / p('documents') / p('archive'))
            mkdir(files / p('projects') / p('archive'))
            mkdir(files / p('notes') / p('archive'))

        if IS_WINDOWS:
            self.links += [
                (
                    self.home / p('.vim'),
                    self.home / p('AppData/Local/nvim')
                ),
            ]

    def stow(self):
        """
        stow and link the specified files
        """
        # pylint: disable=invalid-name
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
    Run dploy unstow unlink all files into their respective repositories
    """
    # pylint: disable=unused-argument
    Dploy().stow()


@task
def unstow(ctx):
    """
    Run dploy stow link all files into their respective repositories
    """
    # pylint: disable=unused-argument
    Dploy().unstow()


@task(provision, stow)
def install(ctx):
    """
    Install task
    """
    # pylint: disable=unused-argument


@task(lint_shell, lint_yaml, lint_python, lint_vim, default=True)
def lint(ctx):
    """
    Lint task
    """
    # pylint: disable=unused-argument
