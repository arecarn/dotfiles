# -                                                                        {{{
##############################################################################
zgen_dir=~/zgen
zgen_file=~/zgen/zgen.zsh

(
if ! [[ -e $zgen_file ]]; then
    git clone https://github.com/tarjoilija/zgen $zgen_dir
fi
)
source $zgen_file

# check if there's no init script
if ! zgen saved; then
    echo "Creating a zgen save"

    zgen oh-my-zsh

    #plugins
    zgen load bundle command-not-found
    zgen load bundle git
    zgen load bundle tmux
    zgen load bundle z
    zgen load bundle zsh-users/zsh-completions src
    # start maintain ordering
    zgen load zsh-users/zsh-syntax-highlighting
    zgen load zsh-users/zsh-history-substring-search
    zgen load tarruda/zsh-autosuggestions
    # end maintain ordering

    # theme
    zgen oh-my-zsh themes/robbyrussell

    # save all to init script
    zgen save
fi

# autosuggestions config
# Enable autosuggestions automatically
zle-line-init() {
    zle autosuggest-start
}
zle -N zle-line-init


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
# bindkey '^P' history-beginning-search-backward
# bindkey '^N' history-beginning-search-forward
bindkey '^P' history-substring-search-up
bindkey '^N' history-substring-search-down

# bindkey -M vicmd '^P' history-beginning-search-backward
# bindkey -M vicmd '^N' history-beginning-search-forward

# bind k and j for VI mode
bindkey -M vicmd '^P' history-substring-search-up
bindkey -M vicmd '^N' history-substring-search-down

# Accept suggestions without leaving insert mode
bindkey '^F' vi-forward-blank-word

# backspace and ^h working even after returning from command mode
bindkey '^?' backward-delete-char
bindkey '^H' backward-delete-char

# ctrl-w removed word backwards
bindkey '^W' backward-kill-word

#starts searching history backward
bindkey '^R' history-incremental-search-backward
# s starts searching history backward
bindkey '^S' history-incremental-search-forward


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
