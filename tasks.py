import os
import fnmatch
from invoke import task
import dploy

# The Python 3.5 glob module supports recursive globs, and the python 3.4
# pathlib module also does, but for version 2.2 to 3.3 this is the work around.
# source: http://stackoverflow.com/a/2186673
def find_files(directory, pattern):
    for root, _, files in os.walk(directory):
        for basename in files:
            if fnmatch.fnmatch(basename, pattern):
                filename = os.path.join(root, basename)
                yield filename

@task
def lint_vim(ctx):
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
    files = []
    files.extend(find_files(directory='ansible', pattern='*.yml'))
    files_string = " ".join(files)

    cmd = 'yamllint --format parsable {files}'
    cmdf = cmd.format(files=files_string)
    print(cmdf)
    ctx.run(cmdf, pty=True)

@task
def lint_python(ctx):
    files = [
        'tasks.py',
    ]

    files_string = ' '.join(files)
    cmd = 'python3 -m pylint --output-format=parseable {files}'
    cmdf = cmd.format(files=files_string)
    print(cmdf)
    ctx.run(cmdf, pty=True)

@task(lint_vim, lint_shell, lint_yaml, lint_python)
def lint(ctx):
    pass

@task
def provision(ctx, args=''):
    os.chdir('ansible')
    ctx.run('ansible-playbook site.yml' + ' ' + args, pty=True)

@task
def clean(ctx):
    ctx.run('git clean --interactive', pty=True)

@task
def setup(ctx):
    ctx.run('pip install -r requirements.txt')

class Dploy():
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

    def do(self):
        dploy.stow(self.packages, self.home)
        for src, dest in self.links:
            dploy.link(os.path.join(*src), os.path.join(*dest))

    def undo(self):
        for _, dest in reversed(self.links):
            os.unlink(os.path.join(*dest))

        dploy.unstow(self.packages, self.home)

@task(name='dploy')
def _dploy(ctx):
    Dploy().do()

@task(name='undploy')
def _undploy(ctx):
    Dploy().undo()
