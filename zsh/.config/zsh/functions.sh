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

