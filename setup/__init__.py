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
from setup.util import get_absolute_dirname

# ============================================================================
def backup(dotfiles, dotfiles_directory):

    dotfiles_directory_name = os.path.basename(dotfiles_directory)

    backup_location = get_absolute_dirname(dotfiles_directory)

    backup_dir = os.path.join(backup_location, time_stamped(dotfiles_directory_name))

    print("Backing Up Old Dotfiles Into {0}".format(backup_dir))
    os.mkdir(backup_dir)

    for dotfile in dotfiles:
        target = resolve_abs_path(dotfile["location"])

        dotfile_basename = os.path.basename(dotfile["location"])
        dest = os.path.join(backup_dir, dotfile_basename)

        try:
            print("Moving {target} into {dest}".format(target=target, dest=dest))
            shutil.move(target, dest)
        except Exception as exception_message:
            print(exception_message)


def symlink_files(dotfiles, dotfiles_directory):
    print("Symbolic Linking Files")

    for dotfile in dotfiles:

        dest = resolve_abs_path(dotfile["location"])

        dotfile_location_directory = os.path.dirname(dest)

        source_name = resolve_path(dotfile["source"])
        source_path = os.path.join(dotfiles_directory, source_name)
        source_path_absolute =  resolve_abs_path(source_path)

        # get a relative path to the source from the destination location of
        # the dotfile, this way we will have a relative symlink
        source_path_relative = os.path.relpath(
                source_path_absolute,
                start=dotfile_location_directory)

        print("Creating link {dest} pointing to {source}".format(
            source=source_path_relative,
            dest=dest))

        try:
            os.symlink(source_path_relative, dest)
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


