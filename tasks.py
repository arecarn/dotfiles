"""
Project Tasks that can be invoked using using the program "invoke" or "inv"
"""

import os
import fnmatch
from invoke import task
import dploy

IS_WINDOWS = os.name == 'nt'
if IS_WINDOWS:
    # setting 'shell' is a work around for issue #345 of invoke
    RUN_ARGS = {'pty': False, 'shell': r'C:\Windows\System32\cmd.exe'}
    STOW_LOCATION = 'USERPROFILE'
else:
    RUN_ARGS = {'pty': True}
    STOW_LOCATION = 'HOME'


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

    files_string = ' '.join(files)
    cmd = 'python3 -m pylint --output-format=parseable {files}'
    ctx.run(cmd.format(files=files_string), **RUN_ARGS)


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
    os.chdir('ansible')
    ctx.run('ansible-playbook site.yml --ask-vault-pass --inventory localhost --ask-become-pass ' + ' ' + args,
            **RUN_ARGS)


@task
def clean(ctx):
    """
    Clean repository using git
    """
    ctx.run('git clean --interactive', **RUN_ARGS)


@task
def setup(ctx, args=''):
    """
    Install python requirements
    """
    ctx.run('pip install ' + args + ' --requirement requirements.txt', **RUN_ARGS)


class Dploy():
    """
    Class to handle logic and data to stow and unstow using dploy
    """
    def __init__(self):
        self.home = os.environ[STOW_LOCATION]
        self.packages = [
            'cmd',
            'ctags',
            'git',
            'mutt',
            'readline',
            'scripts',
            'tmux',
            'vim',
            'zsh'
        ]

        self.links = [
            ((self.home, '.vim', 'vimrc'), (self.home, '.vimrc')),
            ((self.home, '.vim'), (self.home, 'vimfiles')),
            ((self.home, '.vim', 'vimrc'), (self.home, '.vim', 'init.vim')),
            ((self.home, '.vim', 'vimrc'), (self.home, '.vim', 'init.vim')),
            ((self.home, '.vim'), (self.home, '.config', 'nvim')),
        ]
        if IS_WINDOWS:
            self.links += [((self.home, '.vim'), (self.home, 'AppData', 'Local', 'nvim'))]

    def stow(self):
        """
        stow and link the specified files
        """
        # pylint: disable=invalid-name
        dploy.stow(self.packages, self.home, is_silent=False)
        for src, dest in self.links:
            dploy.link(os.path.join(*src), os.path.join(*dest), is_silent=False)

    def unstow(self):
        """
        unstow and link the specified files
        """
        for _, dest in reversed(self.links):
            try:
                os.unlink(os.path.join(*dest))
            except FileNotFoundError:
                pass

        dploy.unstow(self.packages, self.home, is_silent=False)


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
    pass


@task(lint_shell, lint_yaml, lint_python, default=True)
def lint(ctx):
    """
    Lint task
    """
    # pylint: disable=unused-argument
    pass
