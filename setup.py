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

BACKUP_DIR = os.path.join(HOME, time_stamped(DOTFILES_DIR))

FILES = [
    os.path.join(HOME, ".zshrc_local"),
    os.path.join(HOME, ".vimrc_local"),
    os.path.join(HOME, ".gitconfig_local"),
]

DIRECTORIES = [
    os.path.join(HOME, ".Trash"),
]

DOTFILES = [
        {
            "source" : ".ctags",
            "name" : ".ctags",
            "location" : HOME,
        },


        {
            "source" : ".gitconfig",
            "name" : ".gitconfig",
            "location" : HOME,
        },
        {
            "source" : ".gitignore_global",
            "name" : ".gitignore_global",
            "location" : HOME,
        },


        {
            "source" : ".inputrc",
            "name" : ".inputrc",
            "location" : HOME,
        },
        {
            "source" : ".mutt",
            "name" : ".mutt",
            "location" : HOME,
        },


        # Tmux
        {
            "source" : ".tmux",
            "name" : ".tmux",
            "location" : HOME,
        },
        {
            "source" : os.path.join(".tmux", ".tmux.conf"),
            "name" : ".tmux.conf",
            "location" : HOME,
        },

        # Vim
        {
            "source" : ".vim",
            "name" : ".vim",
            "location" : HOME,
        },
        {
            "source" : os.path.join(".vim", "vimrc"),
            "name" : ".vimrc",
            "location" : HOME,
        },
        {
            "source" : '.vim',
            "name" : "vimfiles",
            "location" : HOME,
        },

        # Z-Shell
        {
            "source" : ".zsh",
            "name" : ".zsh",
            "location" : HOME,
        },
        {
            "source" : os.path.join(".zsh", ".zshrc"),
            "name" : ".zshrc",
            "location" : HOME,
        },
]

def backup(dotfiles, backup_dir):
    print("Backing Up Old Dotfiles Into {0}".format(backup_dir))
    os.mkdir(backup_dir)

    for dotfile in dotfiles:
        target = os.path.join(dotfile["location"], dotfile["name"])
        dest = os.path.join(backup_dir, dotfile["name"])

        try:
            print("Moving {target} into {dest}".format(target=target, dest=dest))
            shutil.move(target, dest)
        except Exception as exception_message:
            print(exception_message)


def symlink_files(dotfiles, dotfiles_dir):
    print("Symbolic Linking Files")

    for dotfile in dotfiles:
        source = os.path.join(dotfiles_dir, dotfile["source"])
        dest = os.path.join(dotfile["location"], dotfile["name"])
        print("Creating link {dest} pointing to {source}".format(source=source, dest=dest))

        try:
            os.symlink(source, dest)
        except Exception as exception_message:
            print(exception_message)


def create_files(config_files):
    print("Creating Local Config Files")

    for config_file in config_files:
        print("Creating config file if it doesn't already exist: {0}".format(config_file))

        try:
            with open(config_file, "a+") as file:
                pass
        except Exception as exception_message:
            print(exception_message)


def create_directories(directories):
    print("Creating Directories")

    for directory in directories:
        print("Creating Directory: {0}".format(directory))

        try:
            os.makedirs(directory)
        except Exception as exception_message:
            print(exception_message)


if __name__ == '__main__':
    backup(DOTFILES, BACKUP_DIR)
    print("\n")

    symlink_files(DOTFILES, DOTFILES_DIR)
    print("\n")

    create_files(FILES)
    print("\n")

    create_directories(DIRECTORIES)
    print("\n")

    print("FIN")
