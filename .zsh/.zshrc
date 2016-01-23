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

n="$HOME/Dropbox/notes/"
df="$HOME/dotfiles"

###########################################################################}}}
# PLUGINS                                                                  {{{
##############################################################################
zplug_file=~/.zplug/zplug

if ! [[ -e $zplug_file ]]; then
    curl -fLo ~/.zplug/zplug --create-dirs https://git.io/zplug
fi

source $zplug_file > /dev/null

zplug "plugins/command-not-found", from:oh-my-zsh
zplug "plugins/tmux", from:oh-my-zsh
zplug "plugins/ssh-agent", from:oh-my-zsh
zplug "themes/bureau", from:oh-my-zsh

zplug "zsh-users/zsh-completions"
zplug "zsh-users/zsh-syntax-highlighting"
zplug "rupa/z", of:"*.sh"

# Install plugins if there are plugins that have not been installed
if ! zplug check --verbose > /dev/null; then
    printf "Install? [y/n]: "
    if read -q; then
        echo; zplug install
    fi
fi

# Then, source plugins and add commands to $PATH
zplug load --verbose > /dev/null
# let zplug manage itself
zplug update --self > /dev/null

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
autoload -U compinit
compinit

unsetopt menu_complete # unset as to not to collide with auto_menu
setopt auto_menu # use menu completion after the second consecutive request for completion
setopt complete_in_word # keep the cursor in place until a completion
setopt always_to_end # move the cursor to end after completion
setopt auto_param_slash # add a trailing slash instead of a space
setopt list_types # List files like "ls -F"
setopt glob_complete # open completion on globs
setopt glob_dots # do not require a leading `.' in filename to be matched

# use completion menu, where select is the number of items needed for the menu
# to open
zstyle ':completion:*' menu select=1 _complete _ignored _approximate

# Completion Styles

# list of completion types to use
zstyle ':completion:*::::' completer _expand _complete _ignored _approximate

# allow one error for every three characters typed in approximate completer
zstyle ':completion:*:approximate:*' max-errors 3

# Formatting and messages
zstyle ':completion:*' verbose yes
zstyle ':completion:*:matches' group yes
zstyle ':completion:*:options' description yes
zstyle ':completion:*:descriptions' format "$fg[yellow]%B-- %d --%b"
zstyle ':completion:*:messages' format '%d'
zstyle ':completion:*:warnings' format "$fg[red]No matches for:$reset_color %d"
zstyle ':completion:*:corrections' format '%B%d (errors: %e)%b'
zstyle ':completion:*' group-name ''
zstyle ':completion:*:options' auto-description '%d'

# when doing an expansion use a custom order of tags
zstyle ':completion:*:expand:*' group-order original all-expansions expansions

# match uppercase from lowercase, and left-side substrings
zstyle ':completion:*' matcher-list 'm:{a-z}={A-Z}' '+l:|=*'

# command completion: highlight matching part
zstyle -e ':completion:*:default' list-colors 'reply=( '\''=(#b)('\''$words[CURRENT]'\''|)*-- #(*)=0=38;5;45=38;5;136'\'' '\''=(#b)('\''$words[CURRENT]'\''|)*=0=38;5;45'\'' )'

# use LS_COLORS for file coloring
zstyle ':completion:*' list-colors ${(s.:.)LS_COLORS}

# show command short descriptions, too
zstyle ':completion:*' extra-verbose yes
# make them a little less short, after all (mostly adds -l option to the whatis calll)
zstyle ':completion:*:command-descriptions' command '_call_whatis -l -s 1 -r .\*; _call_whatis -l -s 6 -r .\* 2>/dev/null'

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

alias gp="grep -P"
alias py="python"
alias p="$PAGER"

alias so="source"
alias soz="source ~/dotfiles/.zsh/.zshrc"
alias sot="tmux source-file ~/dotfiles/.tmux/.tmux.conf"

alias e="$EDITOR"
alias ez="$EDITOR ~/dotfiles/.zsh/.zshrc"
alias eg="$EDITOR ~/dotfiles/.gitconfig"
alias egs='$EDITOR $(git status --porcilean | cut -c 4- | fzf -m)'
alias ev="$EDITOR ~/dotfiles/.vim/vimrc"
alias et="$EDITOR ~/dotfiles/.tmux/.tmux.conf"
alias todo="$EDITOR ~/Dropbox/notes/todo.txt"

alias mk="mkdir"
alias rd="rmdir"
alias rmr="rm -rI"

# shortcuts to tar and compress
alias targz="tar -zcvf"
alias tarbz2="tar -jcvf"
alias tarxz="tar -Jcvf"
# extract tar archive even if it has been compressed (e.g. .gz, .xz, bz2)
alias untar="tar -xvf"

alias df="df -h"
alias du="du -hc"
# disk usage sorted
alias dus="du -hsxc *(D) | sort -rh"

alias g="git"
alias v="vim"

alias l="ls -paF"
alias ll="l -lh"
alias ld="l -d *(/D)"
alias lld="ld -lh *(/D)"

alias t="pwd; tree -a"
alias tt="t -ph"
alias td="t -d"
alias ttd="tt -d"

alias tsh="~/dotfiles/mybin/scripts/trash.sh"
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
