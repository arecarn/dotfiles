from invoke import task, run
import dploy
import os

@task
def provision(ctx):
    ctx.run('ansible-playbook -i ansible/hosts ansible/site.yml --ask-become-pass', pty=True)

@task
def clean(ctx):
    ctx.run("git clean -x -d --force" % pattern)

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

@task(name="dploy")
def _dploy(ctx):
    Dploy().do()

@task(name="undploy")
def _undploy(ctx):
    Dploy().undo()
