"""
Project Tasks that can be invoked using using the program "invoke" or "inv"
"""

import os
import fnmatch
from invoke import task
import dploy

def find_files(directory, pattern):
    """
    Recursively find files in directory using the glob expression pattern

    The Python 3.5 glob module supports recursive globs, and the python 3.4
    pathlib module also does, but for version 2.2 to 3.3 this is the work around.
    source: http://stackoverflow.com/a/2186673
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
    cmdf = cmd.format(files=files_string)
    print(cmdf)
    ctx.run(cmdf, pty=True)

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
    cmdf = cmd.format(files=files_string)
    print(cmdf)
    ctx.run(cmdf, pty=True)

@task
def lint_yaml(ctx):
    """
    Run yamllint on YAML Ansible configuration files
    """
    files = []
    files.extend(find_files(directory='ansible', pattern='*.yml'))
    files_string = " ".join(files)

    cmd = 'yamllint --format parsable {files}'
    cmdf = cmd.format(files=files_string)
    print(cmdf)
    ctx.run(cmdf, pty=True)

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
    cmdf = cmd.format(files=files_string)
    print(cmdf)
    ctx.run(cmdf, pty=True)

@task
def provision_all(ctx, args=''):
    """
    Provision this and other system using ansible
    """
    os.chdir('ansible')
    ctx.run('ansible-playbook site.yml --ask-vault-pass --inventory hosts' + ' ' + args,
            pty=True)

@task
def provision(ctx, args=''):
    """
    Provision this and other system using ansible
    """
    os.chdir('ansible')
    ctx.run('ansible-playbook site.yml --ask-vault-pass --inventory localhost --ask-become-pass ' + ' ' + args,
            pty=True)

@task
def clean(ctx):
    """
    Clean repository using git
    """
    ctx.run('git clean --interactive', pty=True)

@task
def setup(ctx):
    """
    Install python requirements
    """
    ctx.run('pip install -r requirements.txt')

class Dploy():
    """
    Class to handle logic and data to stow and unstow using dploy
    """
    def __init__(self):
        self.home = os.environ['HOME']
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
            ((self.home, '.vim'), (self.home, '.config', 'nvim')),
        ]

    def stow(self):
        """
        stow and link the specified files
        """
        # pylint: disable=invalid-name
        dploy.stow(self.packages, self.home)
        for src, dest in self.links:
            dploy.link(os.path.join(*src), os.path.join(*dest))

    def unstow(self):
        """
        unstow and link the specified files
        """
        for _, dest in reversed(self.links):
            os.unlink(os.path.join(*dest))

        dploy.unstow(self.packages, self.home)

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

@task(lint_vim, lint_shell, lint_yaml, lint_python, default=True)
def lint(ctx):
    """
    Lint task
    """
    # pylint: disable=unused-argument
    pass
