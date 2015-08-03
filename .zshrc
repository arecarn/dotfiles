# -                                                                        {{{
##############################################################################
source ~/antigen/antigen.zsh

antigen bundle git
antigen use oh-my-zsh
antigen bundle zsh-users/zsh-syntax-highlighting
antigen bundle command-not-found
antigen theme terminalparty
antigen apply

###########################################################################}}}
# LINES CONFIGURED BY ZSH-NEWUSER-INSTALL                                  {{{
##############################################################################
HISTFILE=~/.histfile
HISTSIZE=10000
SAVEHIST=10000

###########################################################################}}}
# General Settings                                                         {{{
##############################################################################
setopt histignoredups # ignore duplicates in history
setopt autonamedirs #
setopt autocd

###########################################################################}}}
# KEY BINDINGS                                                             {{{
##############################################################################
bindkey -v # vi like settings
export KEYTIMEOUT=1

# ctrl-p ctrl-n history navigation
bindkey '^P' history-beginning-search-backward
bindkey '^N' history-beginning-search-forward

# backspace and ^h working even after returning from command mode
bindkey '^?' backward-delete-char
bindkey '^H' backward-delete-char

# ctrl-w removed word backwards
bindkey '^W' backward-kill-word

#starts searching history backward
bindkey '^R' history-incremental-search-backward
# s starts searching history backward
bindkey '^S' history-incremental-search-forward

bindkey -M vicmd '^P' history-beginning-search-backward
bindkey -M vicmd '^N' history-beginning-search-forward

bindkey '^E' _expand_alias

###########################################################################}}}
# ALIASES AND SMALL SCRIPTS                                                {{{
##############################################################################
alias pslevel='pstree -s $$'
alias e='vim'
alias g='git'
alias tsh='~/dotfiles/mybin/scripts/trash.sh'
alias nfind='find . -name '
alias minivim='vim -u ~/dotfiles/vim/.vimrc_minimal'

if [[ "$OSTYPE" == "linux-gnu" || "$OSTYPE" == "linux" || "$OSTYPE" == "freebsd"*  ]]; then
    alias open='xdg-open'
elif [[ "$OSTYPE" == "darwin"* ]]; then
elif [[ "$OSTYPE" == "cygwin" ]]; then
    alias open='cygstart'
elif [[ "$OSTYPE" == "win32" ]]; then
    alias open='start'
else
fi

# run a command untill it fails
function untilfail()
{
    while "$@";
    do :
    done
}

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

# -                                                                        {{{
##############################################################################
# vim: textwidth=78
# vim: foldmethod=marker
###########################################################################}}}
