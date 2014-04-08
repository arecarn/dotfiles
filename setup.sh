#!/bin/bash
############################
# setup        
# This script creates symlinks from the home directory to any desired dotfiles
# in ~/dotfiles
############################

########## Variables
# dotfiles directory
dir=~/dotfiles                

# old dotfiles backup directory
olddir=~/dotfiles_old                      

# list of files/folders to symlink in homedir
files="tmux.conf mutt gitconfig zshrc oh-my-zsh vim ctags"

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

echo "Moving custom zsh plugins into place"
ln -s $dir/dotfiles/oh-my-zsh-plugins $dir/oh-my-zsh/custom/plugins
echo "...done"

# run Vim setup
echo "Running Vim Setup"
# start vim loading the vimrc file then close right after
vim -c 'q'
echo "...done"

echo "Done Installing, You're So Cool Now!"
