# ZSHRC                                                                    {{{
##############################################################################
# Path to your oh-my-zsh configuration.
ZSH=$HOME/.oh-my-zsh

# Set name of the theme to load.
# Look in ~/.oh-my-zsh/themes/
# Optionally, if you set this to "random", it'll load a random theme each
# time that oh-my-zsh is loaded.
ZSH_THEME="af-magic"
# ZSH_THEME="terminalparty"

COMPLETION_WAITING_DOTS="true"

# Uncomment following line if you want to disable marking untracked files under
# VCS as dirty. This makes repository status check for large repositories much,
# much faster.
DISABLE_UNTRACKED_FILES_DIRTY="true"

plugins=(git vi-mode geeknote)

source $ZSH/oh-my-zsh.sh

###########################################################################}}}
# USER CONFIGURATION                                                       {{{
##############################################################################

###########################################################################}}}
# LINES CONFIGURED BY ZSH-NEWUSER-INSTALL                                  {{{
##############################################################################
HISTFILE=~/.histfile
HISTSIZE=10000
SAVEHIST=10000
setopt autocd

###########################################################################}}}
# THE FOLLOWING LINES WERE ADDED BY COMPINSTALL                            {{{
##############################################################################
zstyle :compinstall filename '~/.zshrc'
autoload -Uz compinit
compinit

###########################################################################}}}
# General Settings                                                         {{{
##############################################################################
setopt histignoredups
setopt autonamedirs

###########################################################################}}}
# KEY BINDINGS                                                             {{{
##############################################################################
# vi like settings
bindkey -v
export KEYTIMEOUT=1

# ctrl-p ctrl-n history navigation
bindkey '^P' up-history
bindkey '^N' down-history
# backspace and ^h working even after returning from command mode
bindkey '^?' backward-delete-char
bindkey '^H' backward-delete-char
# ctrl-w removed word backwards
bindkey '^W' backward-kill-word

#starts searching history backward
bindkey '^R' history-incremental-search-backward
# s starts searching history backward
bindkey '^S' history-incremental-search-forward

bindkey '^P' history-beginning-search-backward
bindkey '^N' history-beginning-search-forward

bindkey -M vicmd '^P' history-beginning-search-backward
bindkey -M vicmd '^N' history-beginning-search-forward

bindkey '^E' _expand_alias


###########################################################################}}}
# ALIASES                                                                  {{{
##############################################################################
alias pslevel='pstree -s $$'
alias tmux='tmux -2'
alias e='vim'
alias tsh='~/dotfiles/mybin/scripts/trash.sh'
alias nfind='find . -name '
alias minivim='vim -u ~/dotfiles/vim/.vimrc_minimal'

if [[ "$OSTYPE" == "linux-gnu" ]]; then
    alias open='xdg-open'
elif [[ "$OSTYPE" == "freebsd"* ]]; then
    alias open='xdg-open'
elif [[ "$OSTYPE" == "darwin"* ]]; then
elif [[ "$OSTYPE" == "cygwin" ]]; then
    alias open='cygstart'
elif [[ "$OSTYPE" == "win32" ]]; then
    alias open='start'
else
fi

# geeknote aliases/templates
##################
alias gnc='geeknote create -c " " -tg "@" -t ""'

###########################################################################}}}
# PATH                                                                     {{{
##############################################################################

export PATH="$PATH:$HOME/dotfiles/mybin/scripts"

if [[ "$OSTYPE" == "linux-gnu" ]]; then
    export PATH=":/usr/bin/X11:/usr/X11R6/bin:/usr/games:/opt/kde3/bin:/usr/lib/qt3/bin:$PATH"
elif [[ "$OSTYPE" == "freebsd"* ]]; then
elif [[ "$OSTYPE" == "darwin"* ]]; then
    #for home brew
    export MANPATH="/usr/local/man"
    export PATH="/usr/local/bin:$PATH"
elif [[ "$OSTYPE" == "cygwin" ]]; then
elif [[ "$OSTYPE" == "win32" ]]; then
else
fi

###########################################################################}}}
# MISC                                                                     {{{
##############################################################################
export EDITOR='vim'

source ~/.zshrc_local

if [[ $TERM == "xterm" ]]; then
        export TERM=xterm-256color
fi

source ~/.vim/bundle/gruvbox/gruvbox_256palette.sh

# stop flow control in Tmux e.g. freeze with <C-s> and resume with <C-q>
stty -ixon
stty stop undef

# vim: textwidth=78
# vim: foldmethod=marker
