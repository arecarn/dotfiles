alias -g ...="../../"

alias -g send-right="tmux send-keys -t right"
alias -g send-left="tmux send-keys -t left"

del-history-pattern() {
LC_ALL=C sed -i "/$@/d" $HISTFILE
grep "$@" $HISTFILE
}

# this allows aliases to mostly work when using sudo
alias sudo='sudo '

# Pass the list of job numbers (the keys of the $jobstates special associative
# array) to an anonymous function that runs kill with % prepended to the job
# number if its number of arguments is non-zero.
alias kill-jobs='() { (($#)) && kill %${^@}; } ${(k)jobstates}'

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

alias g='git'
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
alias t1='pwd; tree -L 1'
alias tt='t -ph'
alias tt1='t -ph -L 1'
alias td='t -d'
alias td1='t -d -L 1'
alias ttd='tt -d'
alias ttd1='tt -d -L 1'

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
