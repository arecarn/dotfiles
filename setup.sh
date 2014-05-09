#!/bin/bash
############################
# setup        
# This script creates symlinks from the home directory to any desired dotfiles
# in ~/dotfiles
############################

dir=~/dotfiles                             # dotfiles directory
olddir=~/dotfiles_old                      # old dotfiles backup directory
omzpluginsdir=~/dotfiles/oh-my-zsh/custom/plugins/
omzplugins="geeknote" # list of custome zsh plugins
dotfiles=".inputrc .tmux.conf .mutt .gitconfig .zshrc .oh-my-zsh .vim .ctags" # list of files/folders to symlink in homedir

############################
# Code
############################

echo "Creating Blank Local config files"
touch ~/.zshrc_local ~/.vim/vimrc_local  ~/.Trash ~/.gitconfig_local
echo "...done"

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

echo "Moving oh-my-zsh plugins into $omzpluginsdir "
for file in $omzplugins; do
    echo "Creating symlink to $file in zsh plugins dir "
    ln -s $dir/oh-my-zsh-plugins/$file  $omzpluginsdir/$file
done
echo "...done"

# run Vim setup
echo "Running Vim Setup"
# start vim loading the vimrc file then close right after
vim -c 'q'
echo "...done"

echo "Done Installing, You are So Cool!"

# Pre work for getting rid of submodules  
# git clone git://github.com/VitaliyRodnenko/geeknote.git mybin/installs/geeknote --recursive
# git clone github.com/lpenz/atdtool.git                  mybin/installs/atdtool --recursive

# git clone github.com/s7anley/zsh-geeknote.git           oh-my-zsh-plugins/geeknote --recursive
# git clone github.com/robbyrussell/oh-my-zsh.git         .oh-my-zsh --recursive

# git clone https://github.com/Shougo/neobundle.vim.git   .vim/bundle/neobundle.vim --recursive
# git clone https://github.com/altercation/mutt-colors-solarized.git  mutt/colors/mutt-colors-solarized --recursive
