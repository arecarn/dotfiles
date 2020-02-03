# -                                                                          {{{
################################################################################
# DIRECTORIES
################################################################################
export ZSH_DATA_DIR="${HOME}/.local/share/zsh"
export ZSH_CACHE_DIR="${HOME}/.cache/zsh"
mkdir -p ${ZSH_DATA_DIR}
mkdir -p ${ZSH_CACHE_DIR}

export SH_CONFIG_DIR="${HOME}/.config/shell"
mkdir -p ${SH_CONFIG_DIR}
#############################################################################}}}
# PLUGINS                                                                    {{{
################################################################################
source "${SH_CONFIG_DIR}"/functions.sh

export ZPLUG_HOME="${ZSH_CACHE_DIR}/zplug"
zplug_file="${ZPLUG_HOME}/init.zsh"

if [[ ! -d "${ZPLUG_HOME}" ]]; then
    git clone https://github.com/zplug/zplug "${ZPLUG_HOME}"
fi

zplug-update() {
    cd "${ZPLUG_HOME}"
    git pull
    cd -
}

source "${zplug_file}"

zplug 'plugins/command-not-found', from:oh-my-zsh
zplug 'plugins/tmux', from:oh-my-zsh, defer:1
zplug 'rupa/z', use:'*.sh'
zplug 'zsh-users/zsh-completions'
zplug 'zsh-users/zsh-syntax-highlighting', defer:1
# zplug 'morhetz/gruvbox', use:'gruvbox_256palette.sh'
zplug 'junegunn/fzf', \
    use:"shell", \
    hook-build:'./install --all --no-update-rc --no-key-bindings --xdg --no-bash --no-fish'
zplug 'junegunn/fzf', as:"command", use:"bin/*"
zplug 'pyenv/pyenv', as:"command", use:"bin/*"

# Install plugins if there are plugins that have not been installed
if ! zplug check --verbose; then
    printf 'Install? [y/n]: '
    if read -q; then
        echo; zplug install
    fi
fi

#############################################################################}}}
# PLUGIN CONFIG                                                              {{{
################################################################################

# checks if a plugin is installed via zplug
_is_installed() {
    zplug list | grep -q "$@"
}

if _is_installed 'rupa/z'; then
    local _Z_DATA_DIR="${ZSH_DATA_DIR}/z"
    mkdir -p $_Z_DATA_DIR
    export _Z_DATA="${_Z_DATA_DIR}/data"
fi

if _is_installed 'plugins/ssh-agent'; then
    zstyle :omz:plugins:ssh-agent agent-forwarding on
    zstyle :omz:plugins:ssh-agent identities id_rsa
fi

if _is_installed 'junegunn/fzf'; then
    bindkey -M viins '^T' fzf-file-widget
    bindkey -M viins '^Y' fzf-cd-widget
    bindkey -M viins '^R' fzf-history-widget

    if exists ag; then
        export FZF_DEFAULT_COMMAND='ag --hidden --ignore .git -g ""'
    else
        export FZF_DEFAULT_COMMAND='find .'
    fi
fi

# Finally, source plugins and add commands to ${PATH}
zplug load

if _is_installed 'pyenv/pyenv'; then
    # TODO this might be able to be turned into a hook-load cmd
    # This must happen after 'zplug load' since the pyenv may not be available
    # yet
    export PYENV_ROOT="${ZPLUG_HOME}/repos/pyenv/pyenv"
    eval "$(pyenv init -)"
fi

# enable zsh completion in [n]vim via deoplete.nvim and deoplete-zsh
zmodload zsh/zpty
#############################################################################}}}
# ENVIRONMENT                                                                {{{
################################################################################
if exists nvim; then
    export EDITOR='nvim'
else
    export EDITOR='vim'
fi


export LANG='en_US.UTF-8'

# improved less option
export LESS='--tabs=4 --no-init --LONG-PROMPT --ignore-case --RAW-CONTROL-CHARS'

# configure path
export PATH="${PATH}:${HOME}/bin"

if [[ "${OSTYPE}" == 'darwin'* ]]; then
    # TODO HAVE ansible add these to ~/.profile for homebrew
    export MANPATH="${MANPATH}:/usr/local/man"
    export MANPATH="${MANPATH}:/opt/homebrew/bin"
    export PATH="/usr/local/bin:${PATH}"
    export PATH="/usr/local/opt/llvm/bin:${PATH}"
fi

if [[ ${TERM} == 'xterm' ]]; then
    export TERM=xterm-256color
fi

export zsh="${HOME}/.zshrc"
export zshl="${HOME}/.zshrc_local"
export shf="${SH_CONFIG_DIR}/functions.sh"
export git="${HOME}/.gitconfig"
export gitl="${HOME}/.gitconfig_local"
export vim="${HOME}/.vimrc"
export viml="${HOME}/.vimrc_local"
export tmux="${HOME}/.tmux.conf"
export t="${HOME}/Dropbox/notes/todo.txt"
export i="${HOME}/Dropbox/notes/inbox.md"
export j="${HOME}/Dropbox/notes/journal.md"

f="${HOME}/Dropbox/"
p="${f}/projects/"
n="${f}/notes/"
df="${HOME}/dotfiles/"
dfl="${HOME}/dotfiles_local/"

#############################################################################}}}
# HISTORY OPTIONS                                                            {{{
################################################################################
setopt inc_append_history # save every command before it is executed
setopt share_history # adds history incrementally and share
setopt hist_ignore_dups # ignore duplicates in history
HISTFILE=${ZSH_DATA_DIR}/history
HISTSIZE=500000
SAVEHIST=500000

#############################################################################}}}
# COMPLETION OPTIONS                                                         {{{
################################################################################
autoload -Uz compinit  && compinit -d ~/.zcompdump
zmodload zsh/complist

setopt menu_complete # unset as to not to collide with auto_menu
# setopt auto_menu # use menu completion after the second consecutive request for completion
setopt complete_in_word # keep the cursor in place until a completion
setopt always_to_end # move the cursor to end after completion
setopt auto_param_slash # add a trailing slash instead of a space
setopt list_types # List files like "ls -F"
setopt glob_complete # open completion on globs
setopt glob_dots # do not require a leading `.' in filename to be matched

# Completion Styles

# use completion menu, where select is the number of items needed for the menu
# to open
zstyle ':completion:*' menu yes select _complete _ignored _approximate

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
# make them a little less short, after all (mostly adds -l option to the whatis call)
zstyle ':completion:*:command-descriptions' command '_call_whatis -l -s 1 -r .\*; _call_whatis -l -s 6 -r .\* 2> /dev/null'

#############################################################################}}}
# GENERAL OPTIONS                                                            {{{
################################################################################
setopt auto_name_dirs # allow special ~dirs for shortcuts
setopt auto_cd # just by writing a path
setopt print_exit_value #print non-zero exit codes
setopt interactivecomments # pound sign in interactive prompt
# Display CPU usage stats for commands taking more than REPORTTIME seconds
REPORTTIME=5

# setup automatic directory pushing during cd
setopt auto_pushd
setopt pushd_ignore_dups
setopt pushd_minus

#############################################################################}}}
# KEY BINDINGS                                                               {{{
################################################################################
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

autoload -Uz edit-command-line
zle -N edit-command-line

zle -C complete-menu menu-select _generic
_complete_menu() {
    setopt localoptions alwayslastprompt
    zle complete-menu
}
zle -N _complete_menu


bindkey -M viins '^A'    beginning-of-line
bindkey -M viins '^E'    end-of-line
bindkey -M viins '^K'    kill-line
bindkey -M viins '^P'    history-beginning-search-backward
bindkey -M viins '^N'    history-beginning-search-forward
bindkey -M viins '^/'    undo
bindkey -M viins '^W'    _backward-kill-word-and-split-undo
bindkey -M viins '^U'    _backward-kill-line-and-split-undo
bindkey -M viins '^H'    _backward-delete-char-and-split-undo
bindkey -M viins '^?'    _backward-delete-char-and-split-undo
bindkey -M viins '^X'    _expand_alias
bindkey -M viins '^K'    insert-last-word
bindkey -M viins '^O'    _insert-next-word
bindkey -M viins '^S'    copy-prev-shell-word
bindkey -M viins '^X^R'  redisplay
bindkey -M viins '\eOH'  beginning-of-line # Home
bindkey -M viins '\eOF'  end-of-line # End
bindkey -M viins '\e[2~' overwrite-mode # Insert
bindkey -M viins '^F'    forward-char
bindkey -M viins '^B'    backward-char
bindkey -M viins '^V'    edit-command-line
bindkey -M viins '^G'    _complete_menu
bindkey -M viins '^Q'    push-line
# }}}

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
bindkey -M vicmd '^/'    undo
bindkey -M vicmd u       undo
bindkey -M vicmd '^R'    redo
bindkey -M vicmd '^F'    forward-char
bindkey -M vicmd '^B'    backward-char
bindkey -M vicmd g~      vi-oper-swap-case
bindkey -M vicmd gg      beginning-of-buffer-or-history
bindkey -M vicmd G       end-of-buffer-or-history
bindkey -M vicmd '^V'    edit-command-line
bindkey -M vicmd '^Q'    push-line
# }}}2

# Menu Selection {{{2
bindkey -M menuselect '^S' history-incremental-search-forward
bindkey -M menuselect '^R' history-incremental-search-backward
bindkey -M menuselect '^?' backward-delete-char
bindkey -M menuselect '^/' undo
bindkey -M menuselect '^[[Z' reverse-menu-complete # Shift Tab
bindkey -M menuselect '^Y' accept-and-infer-next-history
bindkey -M menuselect '^N' down-line-or-history
bindkey -M menuselect '^P' up-line-or-history
bindkey -M menuselect '^B' backward-char
bindkey -M menuselect '^F' forward-char # }}}2

#############################################################################}}}
# ALIASES AND SMALL SCRIPTS                                                  {{{
################################################################################
alias -g ...="../../"

alias -g send-right="tmux send-keys -t right"
alias -g send-left="tmux send-keys -t left"

# this allows aliases to mostly work when using sudo
alias sudo='sudo '

alias gp='grep -P'
alias py='python'
alias p="${PAGER}"

alias so='source'
alias sotmux='tmux source-file ~/.tmux.conf'

alias e="${EDITOR}"

alias mk='mkdir'
alias rd='rmdir'
alias wipe='rm -rf'

# follow symbolic link
alias fln='cd $(readlink -f ./)'

# shortcuts to tar and compress
# usage: tar* ARCHIVE DIR
alias targz='tar -zcvf'
alias tarbz2='tar -jcvf'
alias tarxz='tar -Jcvf'
# extract tar archive even if it has been compressed (e.g. .gz, .xz, bz2)
alias untar='tar -xvf' # usage: untar ARCHIVE

alias df='df -h'
alias du='du -hc'
# disk usage sorted
alias dus='du -hsxc ./* | sort -rh'

alias g='git'
# Git: current branch
alias -g gcb='$(git symbolic-ref --short HEAD)'
alias gnp='git --no-pager'
alias gcd='cd $(git rev-parse --show-toplevel)'
alias v='vim'
alias m="make"

if [[ "${OSTYPE}" == 'linux'* ]]; then
    alias ls='ls --color=auto'
elif [[ "${OSTYPE}" == 'darwin'* ]]; then
    alias ls='ls -G'
fi

alias l='ls -paF'
alias ll='l -lh'
alias ld='l -d *(/D)'
alias lld='ld -lh *(/D)'

alias t='pwd; tree'
alias tt='t -ph'
alias td='t -d'
alias ttd='tt -d'

if [[ "${OSTYPE}" == 'linux'* ]]; then
    alias open="xdg-open"
elif [[ "${OSTYPE}" == 'cygwin' ]]; then
    alias open="cygstart"
elif [[ "${OSTYPE}" == 'win32' ]]; then
    alias open="start"
fi

if [[ "${OSTYPE}" == 'linux'* ]]; then
    alias rcp='rsync --archive --progress --hard-links --acls --xattrs'
elif [[ "${OSTYPE}" == 'darwin'* ]]; then
    alias rcp='rsync -aHE'
fi

alias sa="ssh_start_agent"

# GLOBAL ABBERVIATIONS {{{2
typeset -Ag abbreviations
abbreviations=(
'\\h'   'HEAD__CURSOR__'
'Ia'    '| awk'
'Ig'    '| grep -P'
'Igv'   '| grep -Pv' #inverse match
'Ih'    '| head'
'Im'    '| more'
'Ip'    '| "${PAGER}"'
'Is'    '| sort'
'Ist'   '| sed'
'It'    '| tail'
'Iv'    '| vim -R -'
'Iw'    '| wc'
'Ix'    '| xargs'
)

magic-abbrev-expand() {
    local MATCH
    LBUFFER=${LBUFFER%%(#m)[_a-zA-Z0-9\\]#}
    command=${abbreviations[${MATCH}]}
    LBUFFER+=${command:-${MATCH}}

    if [[ "${command}" =~ '__CURSOR__' ]]
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

bindkey -M viins ' ' magic-abbrev-expand
bindkey -M viins '^ ' no-magic-abbrev-expand
bindkey -M isearch ' ' self-insert
# }}}2

#############################################################################}}}
# TMUX                                                                       {{{
################################################################################
# By default tmux updates the DISPLAY and SSH_AUTH_SOCK variables in tmux's
# own environment, so we have to propagate the environment to our shell.
if [ -n "$TMUX" ]; then
    tmux_refresh_env() {
        export $(tmux show-environment | grep "^SSH_AUTH_SOCK")
        export $(tmux show-environment | grep "^DISPLAY")

        # need to authorize
        # see https://kerneltalks.com/troubleshooting/mobaxterm-x11-proxy-authorisation-not-recognised/
        xauth add $(xauth -f ~/.Xauthority list | tail -1)
    }
else
    tmux_refresh_env() { }
fi

# this is called after reading a command but before executing it
preexec() {
    tmux_refresh_env
}

#############################################################################}}}
# PROMPT                                                                     {{{
################################################################################
setopt prompt_subst
autoload -Uz vcs_info
zstyle ':vcs_info:*' stagedstr 'M'
zstyle ':vcs_info:*' unstagedstr 'M'
zstyle ':vcs_info:*' check-for-changes true
zstyle ':vcs_info:*' actionformats '%F{green}±%b%f %F{red}%a %m%f'
zstyle ':vcs_info:*' formats       '%F{green}±%b%f %m%F{green}%c%f%F{red}%u%f'
zstyle ':vcs_info:git*+set-message:*' hooks git-untracked git-aheadbehind git-stash
zstyle ':vcs_info:*' enable git

+vi-git-untracked() { # {{{2
local number_of_untracked_files=$(git ls-files --other --directory --exclude-standard --no-empty-directory 2> /dev/null | wc -l | tr -d ' ')

if [[ $number_of_untracked_files != 0 ]]; then
    hook_com[unstaged]+='%F{red}??%f'
fi
} # }}}2

### git: Show +N/-N when your local branch is ahead-of or behind remote HEAD.
# Make sure you have added misc to your 'formats': %m
+vi-git-aheadbehind() { # {{{2
local ahead=$(git rev-list ${hook_com[branch]}@{upstream}..HEAD 2> /dev/null | wc -l | tr -d ' ')
local behind=$(git rev-list HEAD..${hook_com[branch]}@{upstream} 2> /dev/null | wc -l | tr -d ' ')
local -a gitstatus

(($ahead)) && gitstatus+=(" %B%F{blue}+${ahead}%f%b")
(($behind)) && gitstatus+=("%B%F{red}-${behind}%f%b")
hook_com[misc]+=${(j::)gitstatus}
} # }}}2

# Show count of stashed changes
+vi-git-stash() { # {{{2
if [[ -s ${hook_com[base]}/.git/refs/stash ]]; then
    local stashes=$(git stash list 2> /dev/null | wc -l | tr -d ' ')
    hook_com[misc]+=" %F{yellow}#${stashes}%f"
fi
} # }}}2

VI_INSERT_MODE='-- INSERT --'
VI_OTHER_MODES='            '
PROMPT_VALUE='${VI_MODE} %~ ${TIME_STAMP} %# '

set-prompt(){ # {{{2
    case ${KEYMAP} in
        viins|main)
            VI_MODE="${VI_INSERT_MODE}";;
        *)
            VI_MODE="${VI_OTHER_MODES}";;
    esac
    PROMPT="${PROMPT_VALUE}"
} # }}}2

precmd(){ # {{{2
    vcs_info
    print ""
    print -rP "%n%F{blue}@%m%f ${vcs_info_msg_0_}"
    VI_MODE="${VI_INSERT_MODE}"
    TIME_STAMP=$(date +"%T")
    PROMPT="${PROMPT_VALUE}"
} # }}}2

zle-line-init() zle-keymap-select() { # {{{2
    set-prompt
    zle reset-prompt
}
zle -N zle-line-init
zle -N zle-keymap-select
# }}}2

#############################################################################}}}
# MISC                                                                       {{{
################################################################################

# stop flow control in Tmux e.g. freeze with <C-s> and resume with <C-q>
stty -ixon
stty stop undef

zshrc_local="${HOME}/.zshrc_local"
if [[ -e "${zshrc_local}" ]] then;
    source "${zshrc_local}"
fi

#############################################################################}}}
# -                                                                          {{{
################################################################################
# vim: textwidth=80
# vim: foldmethod=marker
#############################################################################}}}
