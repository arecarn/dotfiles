#!/bin/sh

# check if a command exists
exists(){
    command -v "$1" > /dev/null 2>&1
}

# check the wather
weather(){
    curl wttr.in/"$@"
}

# follow a symbolic link
lnfl()
{
    (
    link="$*"

    if [ -z "${link}" ]; then
        link=$(pwd)
    fi

    if [ ! -d "${link}" ] || [ ! -L "${link}" ]; then
        echo "lnfl: ${link} is not a valid link"
        return 1
    fi

    link_location=$(readlink -f "${link}")
    cd "${link_location}" || return 1
    )
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

nmodd()
{
    _nmod 777 "$@"
}

nmodf()
{
    _nmod 666 "$@"
}

# beep once if the command succeeds and twice if it fails
# usage "some-comand; testbeep
testbeep() {
    if [  $? -eq 0 ]; then
        echo -e '\a'
    else
        echo -e '\a'
        sleep 0.5
        echo -e '\a'
    fi
}

start-ssh-agent() {
    eval $(ssh-agent -s)
    ssh-add ~/.ssh/id_rsa
}
