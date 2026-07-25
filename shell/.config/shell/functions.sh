#!/bin/sh

bwu() {
    BW_SESSION="$(bw unlock --raw)"
    export BW_SESSION
}

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

# check the weather
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
    cd "$(pwd -P)" || return 1
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
    printf '%s\n' "chmod ${permissions} ${*}"
    chmod "${permissions}" "$@"
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
