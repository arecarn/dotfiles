#!/bin/bash
############################
# setup        
# This script creates symlinks from the home directory to any desired dotfiles
# in ~/dotfiles
############################

dir=~/dotfiles                             # dotfiles directory
olddir=~/dotfiles_old                      # old dotfiles backup directory
dotfiles=".inputrc .tmux.conf .mutt .gitconfig .zshrc .oh-my-zsh .vim .ctags" # list of files/folders to symlink in homedir

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

grab https://github.com/lpenz/atdtool.git                     "mybin/installs/atdtool"
grab https://github.com/robbyrussell/oh-my-zsh.git            ".oh-my-zsh"
grab https://github.com/s7anley/zsh-geeknote.git              "~/dotfiles/oh-my-zsh/custom/plugins/geeknote"
grab https://github.com/Shougo/neobundle.vim.git              ".vim/bundle/neobundle.vim"
grab https://github.com/altercation/mutt-colors-solarized.git "mutt/colors/mutt"

############################
# Vim Setup
############################
# run Vim setup
echo "Running Vim Setup"
# start vim loading the vimrc file then close right after
vim -c 'q'
echo "...done"

echo "Done Installing, You are So Cool!"

