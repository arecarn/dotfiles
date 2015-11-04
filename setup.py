"""
Sets up the dotfiles in this repository

Requires python 3 on Windows
"""

import os
import shutil
import datetime

# ============================================================================

HOME = os.path.relpath(os.path.expanduser("~"))

DOTFILES_DIR = "dotfiles"

def time_stamped(fname, fmt="{fname}_%Y-%m-%d-%H-%M-%S"):
    return datetime.datetime.now().strftime(fmt).format(fname=fname)

DOTFILES_OLD_DIR = os.path.join(HOME, time_stamped("dotfiles_old"))

DOTFILES = [
    ".ctags",
    ".gitconfig",
    ".gitignore_global",
    ".inputrc",
    ".mutt",
    ".tmux",
    ".vim",
    ".zshrc",
]

LOCAL_CONFIG_FILES = [
    os.path.join(HOME, ".zshrc_local"),
    os.path.join(HOME, ".vimrc_local"),
    os.path.join(HOME, ".gitconfig_local"),
]

DIRECTORIES = [
    os.path.join(HOME, ".Trash"),
]

ALIASES = [
        {
            "source" : os.path.join(HOME, '.vim'),
            "target" : os.path.join(HOME, 'vimfiles'),
        },
        {
            "source" : os.path.join(HOME, ".vim", "vimrc"),
            "target": os.path.join(HOME, ".vimrc"),
        },
        {
            "source" : os.path.join(HOME, ".tmux", ".tmux.conf"),
            "target": os.path.join(HOME, ".tmux.conf"),
        },
]

# ============================================================================

print("Backing Up Old Dotfiles Into {0}".format(DOTFILES_OLD_DIR))
os.mkdir(DOTFILES_OLD_DIR)
for dotfile in DOTFILES:
    source = os.path.join(HOME, dotfile)
    target = os.path.join(DOTFILES_OLD_DIR, dotfile)
    try:
        print("Moving {0} into {1}".format(source, target))
        shutil.move(source, target)
    except Exception as exception_message:
        print(exception_message)

print("\n")

print("Symbolic Linking New Dotfiles Into {0}".format(HOME))
for dotfile in DOTFILES:
    source = os.path.join(DOTFILES_DIR, dotfile)
    target = os.path.join(HOME, dotfile)
    print("Creating symbolic link {0} That links to {1}".format(target, source))
    os.symlink(source, target)

print("\n")

print("Creating Local Config Files")
for local_config_file in LOCAL_CONFIG_FILES:
    print("Creating config file if it doesn't already exist: {0}".format(local_config_file))
    try:
        with open(local_config_file, "a+") as file:
            pass
    except Exception as exception_message:
        print(exception_message)

print("\n")

print("Creating Directories")
for directory in DIRECTORIES:
    print("Creating Directory: {0}".format(directory))
    try:
        os.makedirs(directory)
    except Exception as exception_message:
        print(exception_message)

print("\n")

print("Creating File Aliases with Symbolic Links")
for alias in ALIASES:
    source = alias["source"]
    target = alias["target"]
    print("Aliasing {source} to {target}".format(source=source, target=target))
    try:
        os.symlink(source, target)
    except Exception as exception_message:
        print(exception_message)

print("\n")

print("FIN")
