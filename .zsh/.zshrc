# -                                                                        {{{
##############################################################################
export EDITOR='vim'

zgen_dir=~/.zsh/zgen
zgen_file=~/.zsh/zgen/zgen.zsh

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

    zgen oh-my-zsh plugins/command-not-found
    zgen oh-my-zsh plugins/tmux
    zgen oh-my-zsh plugins/ssh-agent
    zgen oh-my-zsh themes/bureau

    zgen load rupa/z
    zgen load zsh-users/zsh-completions src

    zgen save
fi

zstyle :omz:plugins:ssh-agent agent-forwarding on

###########################################################################}}}
# HISTORY                                                                  {{{
##############################################################################
HISTFILE=~/.zsh_history
HISTSIZE=10000
SAVEHIST=10000

###########################################################################}}}
# GENERAL SETTINGS                                                         {{{
##############################################################################
setopt hist_ignore_dups # ignore duplicates in history
setopt auto_name_dirs # allow special ~dirs for shortcuts
setopt auto_cd # just by writing a path
setopt print_exit_value #print non-zero exit codes
exits() {
    command -v "$1" >/dev/null 2>&1
}


# Completion
setopt glob_complete # open completion on globs
setopt glob_dots # do not require a leading `.' in filename to be matched
setopt complete_in_word # Tab completion from both ends

# show ... when doing a rm *
setopt rm_star_wait

# List completion
setopt auto_list
setopt auto_param_slash
setopt auto_param_keys # List like "ls -F"
setopt list_types # Compact completion

# gives you more extensive tab completion TODO(look into this)
autoload -U compinit
compinit

# Tab completion should be case-insensitive.
zstyle ':completion:*' matcher-list 'm:{a-zA-Z}={A-Za-z}'

###########################################################################}}}
# KEY BINDINGS                                                             {{{
##############################################################################
# vi like settings
bindkey -v

# VI MODE KEYBINDINGS (ins mode)
bindkey -M viins '^A'    beginning-of-line
bindkey -M viins '^E'    end-of-line
bindkey -M viins '^K'    kill-line
# bindkey -M viins '^R'    history-incremental-pattern-search-backward
# bindkey -M viins '^S'    history-incremental-pattern-search-forward
bindkey -M viins '^P' history-beginning-search-backward
bindkey -M viins '^N' history-beginning-search-forward
bindkey -M viins '^Y'    yank

backward-kill-word-and-split-undo() {
    zle backward-kill-word
    zle split-undo
}
zle -N backward-kill-word-and-split-undo

backward-kill-line-and-split-undo() {
    zle backward-kill-line
    zle split-undo
}
zle -N backward-kill-line-and-split-undo

backward-delete-char-and-split-undo() {
    zle backward-delete-char
    zle split-undo
}
zle -N backward-delete-char-and-split-undo

insert-next-word() {
    zle insert-last-word 1
}
zle -N insert-next-word

bindkey -M viins '^_'    undo
bindkey -M viins '^W'    backward-kill-word-and-split-undo
bindkey -M viins '^U'    backward-kill-line-and-split-undo
bindkey -M viins '^H'    backward-delete-char-and-split-undo
bindkey -M viins '^?'    backward-delete-char-and-split-undo
bindkey -M viins '^X'    _expand_alias
bindkey -M viins '^K'    insert-last-word
bindkey -M viins '^J'    insert-next-word
bindkey -M viins '^O'    copy-prev-shell-word

bindkey -M viins '^X^R'  redisplay
bindkey -M viins '\eOH'  beginning-of-line # Home
bindkey -M viins '\eOF'  end-of-line       # End
bindkey -M viins '\e[2~' overwrite-mode    # Insert
bindkey -M viins '\ef'   forward-word      # Alt-f
bindkey -M viins '\eb'   backward-word     # Alt-b
bindkey -M viins '\ed'   kill-word         # Alt-d


# VI MODE KEYBINDINGS (cmd mode)
bindkey -M vicmd '^A'    beginning-of-line
bindkey -M vicmd '^E'    end-of-line
bindkey -M vicmd '^P'    history-beginning-search-backward
bindkey -M vicmd '^N'    history-beginning-search-forward
bindkey -M vicmd '^K'    kill-line
bindkey -M vicmd '^Y'    yank
bindkey -M vicmd '^W'    backward-kill-word
bindkey -M vicmd '^U'    backward-kill-line
bindkey -M vicmd '/'     history-incremental-pattern-search-backward
bindkey -M vicmd '?'     history-incremental-pattern-search-forward
bindkey -M vicmd '^_'    undo
bindkey -M vicmd u       undo
bindkey -M vicmd '^R'    redo
bindkey -M vicmd '\ef'   forward-word                      # Alt-f
bindkey -M vicmd '\eb'   backward-word                     # Alt-b
bindkey -M vicmd '\ed'   kill-word                         # Alt-d

export KEYTIMEOUT=1

[ -f ~/.fzf.zsh ] && source ~/.fzf.zsh

###########################################################################}}}
# ALIASES AND SMALL SCRIPTS                                                {{{
##############################################################################

alias so="source"
alias soz="source ~/dotfiles/.zsh/.zshrc"

alias e="$EDITOR"
alias ez="$EDITOR ~/dotfiles/.zsh/.zshrc"
alias eg="$EDITOR ~/dotfiles/.gitconfig"
alias ev="$EDITOR ~/dotfiles/.vim/vimrc"
alias et="$EDITOR ~/dotfiles/.tmux/.tmux.conf"

alias mk="mkdir"
alias rd="rmdir"
alias rmf="rm -rf"

alias gp="grep -P"

alias py="python"

alias du="du -hc"
# disk usage sorted
alias dus="du -hsxc *(D) | sort -rh"

alias g="git"
# Git Files
alias -g  gf='`git status --porcelain | sed -ne "s/^..//p"`'
# Git Modified Files
alias -g  gmf='`git status --porcelain | grep -P "^.M|^[AM]." | sed -ne "s/^..//p"`'
# Git Untracked Files
alias -g  guf='`git status --porcelain | grep -P "^\?\?" | sed -ne "s/^..//p"`'
#TODO handle Git Unmerged Files

alias l="pwd; ls -paF"
alias ll="l -lh"
alias ld="pwd; ls -paFd *(/D)"
alias lld="ld -lh *(/D)"


if exits tree ; then
    alias t="pwd; tree -a"
    alias tt="t -ph"
    alias td="t -d"
    alias ttd="tt -d"
fi
alias tsh="~/dotfiles/mybin/scripts/trash.sh"
alias nfind="find . -name "
alias minivim="vim -u ~/dotfiles/vim/.vimrc_minimal"

if [[ "$OSTYPE" == "linux-gnu" || "$OSTYPE" == "linux" || "$OSTYPE" == "freebsd"*  ]]; then
    alias open="xdg-open"
elif [[ "$OSTYPE" == "darwin"* ]]; then
elif [[ "$OSTYPE" == "cygwin" ]]; then
    alias open="cygstart"
elif [[ "$OSTYPE" == "win32" ]]; then
    alias open="start"
else
fi

# GLOBAL ABBERVIATIONS {{{2
typeset -Ag abbreviations
abbreviations=(
"\\h"   "HEAD__CURSOR__"
"Ia"    "| awk"
"Ig"    "| grep -P"
"Igv"   "| grep -Pv" #inverse match
"Ih"    "| head"
"Ic"    "Hello__CURSOR__! How are you" # cursor example
"Im"    "| more"
"Ip"    "| $PAGER"
"Is"    "| sort"
"Ist"   "| sed"
"It"    "| tail"
"Iv"    "| vim -R -"
"Iw"    "| wc"
"Ix"    "| xargs"
)

magic-abbrev-expand() {
    local MATCH
    LBUFFER=${LBUFFER%%(#m)[_a-zA-Z0-9\\]#}
    command=${abbreviations[$MATCH]}
    LBUFFER+=${command:-$MATCH}

    if [[ "${command}" =~ "__CURSOR__" ]]
    then
        RBUFFER=${LBUFFER[(ws:__CURSOR__:)2]}
        LBUFFER=${LBUFFER[(ws:__CURSOR__:)1]}
    else
        zle self-insert
    fi
    zle split-undo
}

no-magic-abbrev-expand() {
    LBUFFER+=' '
    zle split-undo
}

zle -N magic-abbrev-expand
zle -N no-magic-abbrev-expand
bindkey " " magic-abbrev-expand
bindkey "^ " no-magic-abbrev-expand
bindkey -M isearch " " self-insert
# }}}2


# run a command until it fails
function untilfail()
{
    while "$@";
    do :
    done
}

# find string inclusive
function fin()
{
    local input=$(sed 's/ /|/g' <<< "$@")
    ls -t | grep -iP "$input";
}

# find string exclusive
function fex()
{
    local input="$@"
    input=$(sed 's/ /| grep -iP /g' <<< "$input");
    input=$(sed 's/^/grep -iP /g' <<< $input);
    local cmd='ls -t | '$input
    eval $cmd
}


###########################################################################}}}
# PATH                                                                     {{{
##############################################################################

export PATH="$PATH:$HOME/dotfiles/tools/scripts"

if [[ "$OSTYPE" == "linux-gnu" ]]; then
    export PATH="$PATH:/usr/bin/X11"
    export PATH="$PATH:/usr/X11R6/bin"
    export PATH="$PATH:/usr/games"
    export PATH="$PATH:/opt/kde3/bin"
    export PATH="$PATH:/usr/lib/qt3/bin"
elif [[ "$OSTYPE" == "freebsd"* ]]; then
elif [[ "$OSTYPE" == "darwin"* ]]; then
    #for Homebrew
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
