#!/bin/bash
############################
# setup
# This script creates symlinks from the home directory to any desired dotfiles
# in ~/dotfiles
############################

dir=~/dotfiles                             # dotfiles directory
olddir=~/dotfiles_old                      # old dotfiles backup directory
dotfiles=".inputrc .tmux.conf .mutt .gitconfig .gitignore_global .zshrc .oh-my-zsh .vim .ctags" # list of files/folders to symlink in homedir

############################
# Blank Local Files
############################
echo "Creating Blank Local config files"
touch ~/.zshrc_local ~/.vim/vimrc_local  ~/.Trash ~/.gitconfig_local
echo "...done"


############################
# Symbolic Links
############################
# create dotfiles_old in homedir
echo "Creating $olddir for backup of any existing dotfiles in ~"
mkdir -p $olddir
echo "...done"

# move any existing dotfiles in homedir to dotfiles_old directory, then create symlinks
echo "Moving any existing dotfiles from ~ to $olddir"
for file in $dotfiles; do
    mv ~/$file $olddir/$file
    echo "Creating symlink to $file in home directory."
    ln -s $dir/$file ~/$file
done
echo "...done"

############################
# Git Repo Downloads/Updates
############################
function grab
{
    repo=$1
    location=$2
    echo "For $repo"
    if [ ! -d $location  ]; then # DIRECTORY does not exist
        git clone --recursive $repo "$location"
    else
        cd $location
        git pull --rebase && git submodule update --init --recursive
        echo "in directory $location"
        cd -
    fi
}

############################
# this was pulled from a reddit from user
# http://www.reddit.com/r/vim/comments/28e8z5/simple_vim_plugin_downloader/ciaer2x
# it might be useful
############################
function lookatthis
{
    cnt=0
    cd ~/.vim/bundle &&
        for d in *; do
            if [ -d $d/.git ]; then
                echo "Updating $d"
                cd $d && git pull &
                # Prevent having too many subprocesses
                (( (cnt += 1) % 16 == 0 )) && wait
            fi
        done
        wait
}

grab https://github.com/lpenz/atdtool.git                     "$HOME/dotfiles/mybin/installs/atdtool"
grab https://github.com/robbyrussell/oh-my-zsh.git            "$HOME/dotfiles/.oh-my-zsh"
grab https://github.com/s7anley/zsh-geeknote.git              "$HOME/dotfiles/oh-my-zsh/custom/plugins/geeknote"
grab https://github.com/Shougo/neobundle.vim.git              "$HOME/dotfiles/.vim/bundle/neobundle.vim"
grab https://github.com/altercation/mutt-colors-solarized.git "$HOME/dotfiles/.mutt/colors/mutt"

# move any existing dotfiles in homedir to dotfiles_old directory, then create symlinks
echo "Moving any existing dotfiles from ~ to $olddir"
for file in $dotfiles; do
    mv ~/$file $olddir/$file
    echo "Creating symlink to $file in home directory."
    ln -s $dir/$file ~/$file
done
echo "...done"

############################
# Vim Setup
############################
# run Vim setup
echo "Running Vim Setup"
# start vim loading the vimrc file then close right after
vim -c 'q'
echo "...done"

echo "Done Installing, You are So Cool!"
