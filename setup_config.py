# TODO need a way to source another file, a base config could be used and this
# could help with some defaults?

# TODO allow missing options

# TODO if not specified default to ~/dotfiles?
DOTFILES_DIRECTORY = "~/dotfiles"

# TODO if source isn't specified use name by default?
DOTFILES = [
        {
            "source" : "ctags",
            "location" : "~/.ctags",
        },

        {
            "source" : "git/gitconfig",
            "location" : "~/.gitconfig",
        },

        {
            "source" : "inputrc",
            "location" : "~/.inputrc",
        },

        {
            "source" : "mutt",
            "location" : "~/.mutt",
        },

        {
            "source" : "bin",
            "location" : "~/bin",
        },


        # Tmux
        {
            "source" : "tmux",
            "location" : "~/.tmux",
        },
        {
            "source" : "tmux/tmux.conf",
            "location" : "~/.tmux.conf",
        },

        # Vim
        {
            "source" : "vim",
            "location" : "~/.vim",
        },
        {
            "source" : "vim/vimrc",
            "location" : "~/.vimrc",
        },
        {
            "source" : 'vim',
            "location" : "~/vimfiles",
        },

        # Z-Shell
        {   "source" : "zsh",
            "location" : "~/.zsh",
        },
        {
            "source" : "zsh/zshrc",
            "location" : "~/.zshrc",
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
