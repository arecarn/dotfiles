import argparse

import setup
from setup.util import dynamic_import

parser = argparse.ArgumentParser(description='setup dotfiles')
parser.add_argument(
        "--file",
        default="~/dotfiles/setup_config.py",
        help="path of the setup file")

args = parser.parse_args()
# ============================================================================

setup_config = dynamic_import(args.file, "setup_config")

#TODO use the path of the setup_config file

if __name__ == "__main__":

    setup.backup(
            setup_config.DOTFILES,
            setup_config.DOTFILES_DIR,
            setup_config.DOTFILES_LOCATION)
    print("\n")

    setup.symlink_files(setup_config.DOTFILES, setup_config.DOTFILES_DIR)
    print("\n")

    setup.create_files(setup_config.FILES)
    print("\n")

    setup.create_directories(setup_config.DIRECTORIES)
    print("\n")
