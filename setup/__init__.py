"""
Sets up the dotfiles in this repository

Requires python 3
"""

import sys
import os
import shutil

from setup.util import resolve_abs_path
from setup.util import resolve_path
from setup.util import time_stamped
# ============================================================================
def backup(dotfiles, dotfiles_dir, dotfiles_location):
    location = os.path.expanduser(dotfiles_location)
    backup_dir = os.path.join(location, time_stamped(dotfiles_dir))

    print("Backing Up Old Dotfiles Into {0}".format(backup_dir))
    os.mkdir(backup_dir)

    for dotfile in dotfiles:
        target = os.path.join(dotfile["location"], dotfile["name"])
        target = resolve_abs_path(target)
        dest = os.path.join(backup_dir, dotfile["name"])

        try:
            print("Moving {target} into {dest}".format(target=target, dest=dest))
            shutil.move(target, dest)
        except Exception as exception_message:
            print(exception_message)


def symlink_files(dotfiles, dotfiles_dir):
    print("Symbolic Linking Files")

    for dotfile in dotfiles:
        source_name = resolve_path(dotfile["source"])
        source = os.path.join(dotfiles_dir, source_name)
        dest = os.path.join(dotfile["location"], dotfile["name"])
        dest = resolve_abs_path(dest)
        print("Creating link {dest} pointing to {source}".format(source=source, dest=dest))

        try:
            os.symlink(source, dest)
        except Exception as exception_message:
            print(exception_message)


def create_files(config_files):
    print("Creating Local Config Files")

    for config_file in config_files:
        config_file = resolve_abs_path(config_file)
        print("Creating config file if it doesn't already exist: {0}".format(config_file))

        try:
            with open(config_file, "a+") as file:
                pass
        except Exception as exception_message:
            print(exception_message)


def create_directories(directories):
    print("Creating Directories")

    for directory in directories:
        directory = resolve_abs_path(directory)
        print("Creating Directory: {0}".format(directory))

        try:
            os.makedirs(directory)
        except Exception as exception_message:
            print(exception_message)


