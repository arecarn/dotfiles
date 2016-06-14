#!/bin/sh

# based on: http://stackoverflow.com/a/31443098/2228183

positional_arguments=''
collect_positional_argument(){
    # save all the non-named arguments so they can be reinserted back into the
    # positional parameters at the end of the argument parsing
    positional_arguments="${positional_arguments} '$*'"
}

# default values
name=""
file=""
log=""
default=0

while [ "$#" -gt 0 ]; do
    case "$1" in

        -n|--name)
            name="$2";
            shift 1;;

        -f|--file)
            file="$2";
            shift 1;;

        -l|--log)
            log="$2";
            shift 1;;

        -d|--default)
            default=1;;

        -*)
            echo "unknown option: $1" >&2;
            exit 1;;

        *)
            collect_positional_argument "$1";
    esac
    shift 1
done

# reinsert non-named arguments back into positional parameters ($1 $2 ..)
eval set -- "${positional_arguments}"

echo name = "${name}"
echo file = "${file}"
echo log = "${log}"
echo default = "${default}"

# print the other args
while [ "$#" -gt 0 ]; do
    echo positional argument = "$1"
    shift 1
done
