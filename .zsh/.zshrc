# -                                                                        {{{
###########################################################################}}}
# ENVIRONMENT                                                              {{{
##############################################################################
export EDITOR='vim'

export LANG='en_US.UTF-8'

# improved less option
export LESS='--tabs=4 --no-init --LONG-PROMPT --ignore-case --RAW-CONTROL-CHARS'

# configure path
export PATH="$PATH:$HOME/dotfiles/tools/scripts"
if [[ "$OSTYPE" == "linux"* ]]; then
    export PATH="$PATH:/usr/bin/X11"
    export PATH="$PATH:/usr/X11R6/bin"
    export PATH="$PATH:/usr/games"
    export PATH="$PATH:/opt/kde3/bin"
    export PATH="$PATH:/usr/lib/qt3/bin"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    #for homebrew
    export MANPATH="/usr/local/man"
    export PATH="/usr/local/bin:$PATH"
fi

if [[ $TERM == "xterm" ]]; then
    export TERM=xterm-256color
fi

###########################################################################}}}
# PLUGINS                                                                  {{{
##############################################################################
zplug_file=~/.zplug/zplug

if ! [[ -e $zplug_file ]]; then
    curl -fLo ~/.zplug/zplug --create-dirs https://git.io/zplug
fi

source $zplug_file

zplug "plugins/command-not-found", from:oh-my-zsh
zplug "plugins/tmux", from:oh-my-zsh
zplug "plugins/ssh-agent", from:oh-my-zsh
zplug "themes/bureau", from:oh-my-zsh

zplug "zsh-users/zsh-completions"
zplug "zsh-users/zsh-syntax-highlighting"
zplug "rupa/z", of:"*.sh"

# Install plugins if there are plugins that have not been installed
if ! zplug check --verbose; then
    printf "Install? [y/N]: "
    if read -q; then
        echo; zplug install
    fi
fi

# Then, source plugins and add commands to $PATH
zplug load --verbose
# let zplug manage itself
zplug update --self

zstyle :omz:plugins:ssh-agent agent-forwarding on

###########################################################################}}}
# HISTORY OPTIONS                                                          {{{
##############################################################################
setopt share_history  # adds history incrementally and share
setopt hist_ignore_dups # ignore duplicates in history
HISTFILE=~/.zsh_history
HISTSIZE=10000
SAVEHIST=10000

###########################################################################}}}
# COMPLETION OPTIONS                                                       {{{
##############################################################################
# Completion

# gives you more extensive tab completion
autoload -Uz compinit && compinit

setopt glob_complete # open completion on globs
setopt glob_dots # do not require a leading `.' in filename to be matched
setopt complete_in_word # Tab completion from both ends
setopt auto_list
setopt auto_param_slash
setopt auto_param_keys # List files like "ls -F"
setopt list_types # Compact completion


# list of completion types to use
zstyle ':completion:*::::' completer _expand _complete _ignored _approximate

# use completion menu, where select is the number of items needed for the menu
# to open
zstyle ':completion:*' menu select=1 _complete _ignored _approximate

# completion should be case-insensitive.
zstyle ':completion:*' matcher-list 'm:{a-zA-Z}={A-Za-z}'

# formatting and messages
zstyle ':completion:*' verbose yes
zstyle ':completion:*:descriptions' format '%B%d%b'
zstyle ':completion:*:messages' format '%d'
zstyle ':completion:*:warnings' format 'No matches for: %d'
zstyle ':completion:*:corrections' format '%B%d (errors: %e)%b'
zstyle ':completion:*' group-name ''

###########################################################################}}}
# GENERAL OPTIONS                                                          {{{
##############################################################################
setopt auto_name_dirs # allow special ~dirs for shortcuts
setopt auto_cd # just by writing a path
setopt print_exit_value #print non-zero exit codes
setopt rm_star_wait # add a wait / confirmation when doing a rm *
setopt interactivecomments # pound sign in interactive prompt
# Display CPU usage stats for commands taking more than REPORTTIME seconds
REPORTTIME=10

###########################################################################}}}
# KEY BINDINGS                                                             {{{
##############################################################################
# vi like settings
bindkey -v
export KEYTIMEOUT=1

# Vim Mode (Ins Mode) {{{2
_backward-kill-word-and-split-undo() {
    zle backward-kill-word
    zle split-undo
}
zle -N _backward-kill-word-and-split-undo

_backward-kill-line-and-split-undo() {
    zle backward-kill-line
    zle split-undo
}
zle -N _backward-kill-line-and-split-undo

_backward-delete-char-and-split-undo() {
    zle backward-delete-char
    zle split-undo
}
zle -N _backward-delete-char-and-split-undo

_insert-next-word() {
    zle insert-last-word 1
}
zle -N _insert-next-word

bindkey -M viins '^A'    beginning-of-line
bindkey -M viins '^E'    end-of-line
bindkey -M viins '^K'    kill-line
bindkey -M viins '^P'    history-beginning-search-backward
bindkey -M viins '^N'    history-beginning-search-forward
bindkey -M viins '^_'    undo
bindkey -M viins '^W'    _backward-kill-word-and-split-undo
bindkey -M viins '^U'    _backward-kill-line-and-split-undo
bindkey -M viins '^H'    _backward-delete-char-and-split-undo
bindkey -M viins '^?'    _backward-delete-char-and-split-undo
bindkey -M viins '^X'    _expand_alias
bindkey -M viins '^K'    insert-last-word
bindkey -M viins '^J'    _insert-next-word
bindkey -M viins '^O'    copy-prev-shell-word
bindkey -M viins '^X^R'  redisplay
bindkey -M viins '\eOH'  beginning-of-line # Home
bindkey -M viins '\eOF'  end-of-line       # End
bindkey -M viins '\e[2~' overwrite-mode    # Insert
bindkey -M viins '^F'    forward-character
bindkey -M viins '^B'    back-character # }}}

# Vim Mode (Cmd Mode) {{{2
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
bindkey -M vicmd '^F'    forward-character
bindkey -M vicmd '^B'    back-character #}}}2

# Menu Selection {{{2
zle -C complete-menu menu-select _generic
_complete_menu() {
    setopt localoptions alwayslastprompt
    zle complete-menu
}
zle -N _complete_menu

bindkey '^F' _complete_menu
bindkey -M menuselect '/'  accept-and-infer-next-history
bindkey -M menuselect '^?' undo
bindkey -M menuselect ' ' accept-and-hold
bindkey -M menuselect '*' history-incremental-search-forward
bindkey -M menuselect '^[[Z' reverse-menu-complete # Shift Tab }}}2

[ -f ~/.fzf.zsh ] && source ~/.fzf.zsh

###########################################################################}}}
# ALIASES AND SMALL SCRIPTS                                                {{{
##############################################################################

# check if a command exits
exits() {
    command -v "$1" >/dev/null 2>&1
}

alias so="source"
alias soz="source ~/dotfiles/.zsh/.zshrc"
alias sot="tmux source-file ~/dotfiles/.tmux/.tmux.conf"

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

alias df="df -h"
alias du="du -hc"
# disk usage sorted
alias dus="du -hsxc *(D) | sort -rh"

alias p="$PAGER"

alias g="git"
# Git Files
alias -g gf='`git status --porcelain | sed -ne "s/^..//p"`'
# Git Modified Files
alias -g gmdf='`git status --porcelain | grep -P "^.M|^[AM]." | sed -ne "s/^..//p"`'
# Git Untracked Files
alias -g guf='`git status --porcelain | grep -P "^\?\?" | sed -ne "s/^..//p"`'
#TODO handle Git Unmerged Files

alias l="ls -paF"
alias ll="l -lh"
alias ld="l -d *(/D)"
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

if [[ "$OSTYPE" == "linux"* ]]; then
    alias open="xdg-open"
elif [[ "$OSTYPE" == "cygwin" ]]; then
    alias open="cygstart"
elif [[ "$OSTYPE" == "win32" ]]; then
    alias open="start"
fi


if [[ "$OSTYPE" == "linux"* ]]; then
    alias rsyncp="rsync -aHAX"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    alias rsyncp="rsync -aHE"
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
zle -N magic-abbrev-expand

no-magic-abbrev-expand() {
    LBUFFER+=' '
    zle split-undo
}
zle -N no-magic-abbrev-expand

bindkey -M viins " " magic-abbrev-expand
bindkey -M viins "^ " no-magic-abbrev-expand
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
# MISC                                                                     {{{
##############################################################################
source ~/.vim/bundle/gruvbox/gruvbox_256palette.sh

# stop flow control in Tmux e.g. freeze with <C-s> and resume with <C-q>
stty -ixon
stty stop undef

source ~/.zshrc_local

###########################################################################}}}
# -                                                                        {{{
##############################################################################
# vim: textwidth=78
# vim: foldmethod=marker
###########################################################################}}}
