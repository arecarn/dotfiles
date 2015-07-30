from os.path import join
from os.path import expanduser
from os import name
import os
import datetime

# ============================================================================
HOME = expanduser("~")
dotfiles_dir = join(HOME, "dotfiles")

def time_stamped(fname, fmt="{fname}_%Y-%m-%d-%H-%M-%S"):
    return datetime.datetime.now().strftime(fmt).format(fname=fname)

dotfiles_old_dir = join(HOME, time_stamped("dotfiles_old"))

DOTFILES = [
    ".inputrc",
    ".tmux.conf",
    ".mutt",
    ".gitconfig",
    # ".gitignore_global",
    ".zshrc",
    ".oh-my-zsh",
    ".vim",
    ".ctags",
]

BLANK_FILES = [
    join(HOME, ".zshrc_local"),
    join(HOME, join(".vim", "vimrc_local")),
    join(HOME, ".Trash"),
    join(HOME, ".gitconfig_local"),
]

ALIASES = [
    (join(HOME, '.vim'), join(HOME, 'vimfiles')),
    (join(HOME, ".vim", "vimrc"), join(HOME, ".vimrc")),
]

# ============================================================================

print("Creating {0} for backup of any existing dotfiles in {1}".format(dotfiles_old_dir, HOME))
os.mkdir(dotfiles_old_dir)

print("Moving any existing dotfiles from {0} to {1}".format(dotfiles_dir, dotfiles_old_dir))
for dotfile in DOTFILES:
    source = join(HOME, dotfile)
    target = join(dotfiles_old_dir, dotfile)
    try:
        os.rename(source, target)
    except:
        pass

    print("Symlinking new dotfiles any existing dotfiles from {1} to {0}".format(dotfiles_dir, dotfiles_old_dir))
    source = join(dotfiles_dir, dotfile)
    target = join(HOME, dotfile)
    print("Creating symlink {0}".format(target))
    os.symlink(source, target)

for blank_file in BLANK_FILES:
    print("Creating blank local config file: {0} if needed".format(blank_file))
    open(blank_file, "w")


for alias in ALIASES:
    source = alias[1]
    target = join(dotfiles_old_dir, os.path.basename(alias[1]))
    try:
        os.rename(source, target)
    except:
        pass

    os.symlink(alias[0], alias[1])

print("All Done")
