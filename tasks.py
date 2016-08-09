from invoke import task, run
import dploy
import os
import glob

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
    files = [f for f in glob.iglob(os.path.join('**', '*.yml'), recursive=True)]
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
    ctx.run('git clean -x -d --force' % pattern)

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
        for _ , dest in reversed(self.links):
            os.unlink(os.path.join(*dest))

        dploy.unstow(self.packages, self.home)

@task(name='dploy')
def _dploy(ctx):
    Dploy().do()

@task(name='undploy')
def _undploy(ctx):
    Dploy().undo()
