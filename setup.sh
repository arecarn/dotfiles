#!/bin/bash
############################
# setup        
# This script creates symlinks from the home directory to any desired dotfiles
# in ~/dotfiles
############################

########## Variables
dir=~/dotfiles                    # dotfiles directory
olddir=~/dotfiles_old             # old dotfiles backup directory
files="gitconfig zshrc oh-my-zsh vim" # list of files/folders to symlink in homedir

############################
# Code
############################
# create dotfiles_old in homedir
echo "Creating $olddir for backup of any existing dotfiles in ~"
mkdir -p $olddir
echo "...done"

# move any existing dotfiles in homedir to dotfiles_old directory, then create symlinks 
    echo "Moving any existing dotfiles from ~ to $olddir"
for file in $files; do
    mv ~/.$file ~/dotfiles_old/
    echo "Creating symlink to $file in home directory."
    ln -s $dir/$file ~/.$file
done
for file in $noDotFiles; do
    mv ~/$file ~/dotfiles_old/
    echo "Creating symlink to $file in home directory."
    ln -s $dir/$file ~/$file
done
echo "...done"

# run Vim setup
echo "Running Vim Setup"
rm -Rf $dir/vim/bundle/neobundle.vim/
# install Neobundle to manage plugins
git clone https://github.com/Shougo/neobundle.vim.git $dir/vim/bundle/neobundle.vim
# start vim loading the vimrc file then close right after
vim -c 'q'
echo "...done"

echo "Done Installing, You're So Cool Now!"
