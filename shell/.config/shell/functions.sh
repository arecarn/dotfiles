#!/bin/sh

# check if a command exists
exists(){
    command -v "$1" > /dev/null 2>&1
}

# add a path to the front (default) or end of $PATH if it is not already in
# $PATH
add_to_path () {
    if ! echo "$PATH" | /bin/grep -Eq "(^|:)$1($|:)" ; then
        if [ "$2" = "end" ] ; then
            PATH="$PATH:$1"
        else
            PATH="$1:$PATH"
        fi
    fi
}

# check the wather
weather(){
    curl wttr.in/"$*"
}

# cd to the target directory a symbolic link
cdl()
{
    cd "$(
    link="$*"

    if [ -z "${link}" ]; then
        link=$(pwd)
    fi

    printf '%s' "$(readlink -f "${link}")"
    )" || return 1
}

# cd to the physical location avoiding symlinks
cdp()
{
    cd "$(pwd -P)"
}

# run a command until it fails
untilfail()
{
    while "$@"; do
        :
    done
}


# normalize permissions for files and directories by referring to umask
_nmod()
{
    (
    umask=$(umask)
    permissions="$(($1 - umask))"
    shift
    expression="chmod ${permissions} ${*}"
    print "${expression}"
    eval "${expression}"
    )
}

# normalize permissions for directories
nmodd()
{
    _nmod 777 "$@"
}

# normalize permissions for files
nmodf()
{
    _nmod 666 "$@"
}

# beep once if the command succeeds and twice if it fails
# usage "some-comand; testbeep
testbeep() {
    if [  $? -eq 0 ]; then
        beep
    else
        beep
        beep
        beep
    fi
}

# start the ssh-agent && and prompt for ssh passphrase only after first login
ssh_start_agent() {
    if [ ! -S ~/.ssh/ssh_auth_sock ]; then
      eval "$(ssh-agent)"
      ln -sf "$SSH_AUTH_SOCK" ~/.ssh/ssh_auth_sock
    fi
    export SSH_AUTH_SOCK=~/.ssh/ssh_auth_sock
    ssh-add -l > /dev/null || ssh-add
}
