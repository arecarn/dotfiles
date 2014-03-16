# Path to your oh-my-zsh configuration.
ZSH=$HOME/.oh-my-zsh

# Set name of the theme to load.
# Look in ~/.oh-my-zsh/themes/
# Optionally, if you set this to "random", it'll load a random theme each
# time that oh-my-zsh is loaded.
ZSH_THEME="robbyrussell"

# Example aliases
# alias zshconfig="mate ~/.zshrc"
# alias ohmyzsh="mate ~/.oh-my-zsh"

# Set to this to use case-sensitive completion
# CASE_SENSITIVE="true"

# Uncomment this to disable bi-weekly auto-update checks
# DISABLE_AUTO_UPDATE="true"

# Uncomment to change how often before auto-updates occur? (in days)
# export UPDATE_ZSH_DAYS=13

# Uncomment following line if you want to disable colors in ls
# DISABLE_LS_COLORS="true"

# Uncomment following line if you want to disable autosetting terminal title.
# DISABLE_AUTO_TITLE="true"

# Uncomment following line if you want to disable command autocorrection
# DISABLE_CORRECTION="true"

# Uncomment following line if you want red dots to be displayed while waiting for completion
# COMPLETION_WAITING_DOTS="true"

# Uncomment following line if you want to disable marking untracked files under
# VCS as dirty. This makes repository status check for large repositories much,
# much faster.
# DISABLE_UNTRACKED_FILES_DIRTY="true"

# Uncomment following line if you want to  shown in the command execution time stamp 
# in the history command output. The optional three formats: "mm/dd/yyyy"|"dd.mm.yyyy"|
# yyyy-mm-dd
# HIST_STAMPS="mm/dd/yyyy"

# Which plugins would you like to load? (plugins can be found in ~/.oh-my-zsh/plugins/*)
# Custom plugins may be added to ~/.oh-my-zsh/custom/plugins/
# Example format: plugins=(rails git textmate ruby lighthouse)
plugins=(git geeknote)

source $ZSH/oh-my-zsh.sh

################################################################################
# USER CONFIGURATION
################################################################################

# LINES CONFIGURED BY ZSH-NEWUSER-INSTALL
################################################################################
HISTFILE=~/.histfile
HISTSIZE=1000
SAVEHIST=1000
setopt autocd
# End of lines configured by zsh-newuser-install
################################################################################

# THE FOLLOWING LINES WERE ADDED BY COMPINSTALL
################################################################################
zstyle :compinstall filename '~/.zshrc'
autoload -Uz compinit
compinit
# End of lines added by compinstall
################################################################################

# KEY BINDINGS
################################################################################

# vi like settings
################################################################################
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
# ctrl-r starts searching history backward
bindkey '^R' history-incremental-search-backward
bindkey '^E' _expand_alias


# END OF KEY BINDINGS
################################################################################

# ALIASES
################################################################################
alias tmux='tmux -2'
alias e='vim'
alias trash='~/dotfiles/mybin/scripts/trash.sh'

# geeknote aliases/templates
##################
alias gnc='geeknote create -c " " -tg "@" -t ""'

# END ALIASES
################################################################################

export MANPATH="/usr/local/man:$MANPATH"
export PATH="/usr/local/bin:/usr/bin:/bin:$PATH"

if [[ "$OSTYPE" == "linux-gnu" ]]; then
        # ...
export PATH=":/usr/bin/X11:/usr/X11R6/bin:/usr/games:/opt/kde3/bin:/usr/lib/qt3/bin:$PATH"
elif [[ "$OSTYPE" == "darwin"* ]]; then
        # ...
elif [[ "$OSTYPE" == "cygwin" ]]; then
        # ...
elif [[ "$OSTYPE" == "win32" ]]; then
        # ...
elif [[ "$OSTYPE" == "freebsd"* ]]; then
        # ...
else
        # Unknown.
fi

# EDITOR
################################################################################
export EDITOR='vim'


# LOCAL CONFIG
################################################################################
source ~/.local.zsh
