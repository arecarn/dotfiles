DOTFILES_DIR = "dotfiles"

DOTFILES_LOCATION = "~"

DOTFILES = [
        {
            "source" : ".ctags",
            "name" : ".ctags",
            "location" : "~",
        },

        {
            "source" : ".gitconfig",
            "name" : ".gitconfig",
            "location" : "~",
        },

        {
            "source" : ".gitignore_global",
            "name" : ".gitignore_global",
            "location" : "~",
        },

        {
            "source" : ".inputrc",
            "name" : ".inputrc",
            "location" : "~",
        },

        {
            "source" : ".mutt",
            "name" : ".mutt",
            "location" : "~",
        },


        # Tmux
        {
            "source" : ".tmux",
            "name" : ".tmux",
            "location" : "~",
        },
        {
            "source" : ".tmux/.tmux.conf",
            "name" : ".tmux.conf",
            "location" : "~",
        },

        # Vim
        {
            "source" : ".vim",
            "name" : ".vim",
            "location" : "~",
        },
        {
            "source" : ".vim/vimrc",
            "name" : ".vimrc",
            "location" : "~",
        },
        {
            "source" : '.vim',
            "name" : "vimfiles",
            "location" : "~",
        },

        # Z-Shell
        {   "source" : ".zsh",
            "name" : ".zsh",
            "location" : "~",
        },
        {
            "source" : ".zsh/.zshrc",
            "name" : ".zshrc",
            "location" : "~",
        },
]

FILES = [
    "~/.zshrc_local",
    "~/.vimrc_local",
    "~/.gitconfig_local",
]

DIRECTORIES = [
    "~/.Trash",
]
