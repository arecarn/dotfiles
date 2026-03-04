# History Options
unsetopt extendedhistory # don't include timestamps in history
setopt inc_append_history # save every command before it is executed
setopt share_history # adds history incrementally and share
setopt hist_ignore_dups # ignore duplicates in history
setopt hist_ignore_space # commands with leading spaces are not added to history
HISTFILE=${ZSH_DATA_DIR}/history
HISTSIZE=500000
SAVEHIST=500000

# Completion Options
# Cache compinit for faster startup (regenerate daily)
autoload -Uz compinit
_comp_files=(${ZDOTDIR:-$HOME}/.zcompdump(Nm-20))
if (( $#_comp_files )); then
    compinit -C -d "${ZSH_CACHE_DIR}/zcompdump"
else
    compinit -d "${ZSH_CACHE_DIR}/zcompdump"
fi
unset _comp_files
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

# General Options
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
