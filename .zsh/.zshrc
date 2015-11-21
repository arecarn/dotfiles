# -                                                                        {{{
##############################################################################
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

    zgen oh-my-zsh per-directiory-history #TODO look into configuring this
    zgen oh-my-zsh command-not-found
    zgen oh-my-zsh git
    zgen oh-my-zsh tmux
    zgen oh-my-zsh themes/robbyrussell
    zgen load rupa/z
    zgen load zsh-users/zsh-completions src


    # save all to init script
    zgen save
fi

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
setopt glob_complete # open completion on globs
setopt complete_in_word # Tab completion from both ends

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


# expand aliases
bindkey '^E' _expand_alias

# VI MODE KEYBINDINGS (ins mode)
bindkey -M viins '^A'    beginning-of-line
bindkey -M viins '^E'    end-of-line
bindkey -M viins '^K'    kill-line
bindkey -M viins '^R'    history-incremental-pattern-search-backward
bindkey -M viins '^S'    history-incremental-pattern-search-forward
bindkey -M viins '^P' history-beginning-search-backward
bindkey -M viins '^N' history-beginning-search-forward
bindkey -M viins '^Y'    yank

viins-new-undo-seq() {
    # escape and re-enter to make a new undo sequence
    zle vi-cmd-mode
    zle vi-add-next
}

backward-kill-word-and-new-undo-seq() {
    zle backward-kill-word
    viins-new-undo-seq
}
zle -N backward-kill-word-and-new-undo-seq

backward-kill-line-and-new-undo-seq() {
    zle backward-kill-line
    viins-new-undo-seq
}
zle -N backward-kill-line-and-new-undo-seq

backward-delete-char-and-new-undo-seq() {
    zle backward-delete-char
    viins-new-undo-seq
}
zle -N backward-delete-char-and-new-undo-seq

bindkey -M viins '^_'    undo
bindkey -M viins '^W'    backward-kill-word-and-new-undo-seq
bindkey -M viins '^U'    backward-kill-line-and-new-undo-seq
bindkey -M viins '^H'    backward-delete-char-and-new-undo-seq
bindkey -M viins '^?'    backward-delete-char-and-new-undo-seq



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

[ -f ~/.zsh/fzf.zsh ] && source ~/.zsh/fzf.zsh

###########################################################################}}}
# ALIASES AND SMALL SCRIPTS                                                {{{
##############################################################################

alias so="source"
alias soz="source ~/dotfiles/.zshrc"

alias e="$EDITOR"
alias ez="$EDITOR ~/dotfiles/.zsh/.zshrc"
alias eg="$EDITOR ~/dotfiles/.gitconfig"
alias ev="$EDITOR ~/dotfiles/.vim/vimrc"
alias et="$EDITOR ~/dotfiles/.tmux.conf"

alias mk="mkdir"
alias rd="rmdir"

alias gp="grep -P"

alias py="python"

# disk usage sorted
alias dus="du -hsx *(D) | sort -rh"

alias g="git"
# Git Files
alias -g  gf='`git status --porcelain | sed -ne "s/^..//p"`'
# Git Modified Files
alias -g  gmf='`git status --porcelain | grep -P "^.M|^[AM]." | sed -ne "s/^..//p"`'
# Git Untracked Files
alias -g  guf='`git status --porcelain | grep -P "^\?\?" | sed -ne "s/^..//p"`'
#TODO handle Git Unmerged Files

alias l=" pwd; ls -pa"
alias ll="pwd; ls -palh"

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
"Ia"    "| awk"
"Ig"    "| grep -P"
"Igv"   "| grep -Pv" #inverse match
"Ip"    "| $PAGER"
"Im"    "| more"
"Ih"    "| head"
"It"    "| tail"
"Is"    "| sort"
"Ist"   "| sed"
"Iv"    "| vim -R -"
"Iw"    "| wc"
"Ix"    "| xargs"
"HEAD^" "HEAD\\^"
)

magic-abbrev-expand() {
    local MATCH
    LBUFFER=${LBUFFER%%(#m)[_a-zA-Z0-9^]#}
    LBUFFER+=${abbreviations[$MATCH]:-$MATCH}
    zle self-insert
    viins-new-undo-seq
}

no-magic-abbrev-expand() {
    LBUFFER+=' '
}

zle -N magic-abbrev-expand
zle -N no-magic-abbrev-expand
bindkey " " magic-abbrev-expand
bindkey "^x " no-magic-abbrev-expand
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
