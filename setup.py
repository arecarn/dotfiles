"""
Sets up the dotfiles in this repository

Requires python 3
"""

import os
import datetime

# ============================================================================

HOME = os.path.expanduser("~")

DOTFILES_DIR = os.path.join(HOME, "dotfiles")

def time_stamped(fname, fmt="{fname}_%Y-%m-%d-%H-%M-%S"):
    return datetime.datetime.now().strftime(fmt).format(fname=fname)

DOTFILES_OLD_DIR = os.path.join(HOME, time_stamped("dotfiles_old"))

DOTFILES = [
    ".inputrc",
    ".tmux.conf",
    ".mutt",
    ".gitconfig",
    ".gitignore_global",
    ".zshrc",
    ".vim",
    ".ctags",
]

BLANK_FILES = [
    os.path.join(HOME, ".zshrc_local"),
    os.path.join(HOME, os.path.join(".vim", "vimrc_local")),
    os.path.join(HOME, ".Trash"),
    os.path.join(HOME, ".gitconfig_local"),
]

ALIASES = [
    (os.path.join(HOME, '.vim'), os.path.join(HOME, 'vimfiles')),
    (os.path.join(HOME, ".vim", "vimrc"), os.path.join(HOME, ".vimrc")),
]

# ============================================================================

print("Backing up old dotfiles into {0}".format(DOTFILES_OLD_DIR))
os.mkdir(DOTFILES_OLD_DIR)
for dotfile in DOTFILES:
    source = os.path.join(HOME, dotfile)
    target = os.path.join(DOTFILES_OLD_DIR, dotfile)
    try:
        print("Moving {0} into {1}".format(source, target))
        os.rename(source, target)
    except:
        print("Move failed")
        pass


print("Symlinking new dotfiles into {0}".format(HOME))
for dotfile in DOTFILES:
    source = os.path.join(DOTFILES_DIR, dotfile)
    target = os.path.join(HOME, dotfile)
    print("Creating symlink {0}".format(target))
    os.symlink(source, target)


print("Creating blank local config files")
for blank_file in BLANK_FILES:
    print("Creating config file: {0}".format(blank_file))
    open(blank_file, "w")


print("Creating file aliases")
for alias in ALIASES:
    source = alias[1]
    target = os.path.join(DOTFILES_OLD_DIR, os.path.basename(alias[1]))
    try:
        os.symlink(alias[0], alias[1])
    except:
        pass

print("All Done")
