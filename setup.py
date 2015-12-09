import setup

if __name__ == "__main__":
    setup.backup(setup.DOTFILES, setup.BACKUP_DIR)
    print("\n")

    setup.symlink_files(setup.DOTFILES, setup.DOTFILES_DIR)
    print("\n")

    setup.create_files(setup.FILES)
    print("\n")

    setup.create_directories(setup.DIRECTORIES)
    print("\n")

    print("FIN")
