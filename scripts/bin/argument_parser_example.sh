#!/bin/sh

# based on: http://stackoverflow.com/a/31443098/2228183

# Function to handle required arguments
handle_required_argument() {
    var_name="$1"
    value="$2"
    arg_name="${3}"

    if [ -z "$value" ]; then
        echo "Error: $arg_name requires a value" >&2
        exit 1
    fi

    eval "$var_name='$value'"
}

# Function to check if a required argument is set
check_required_argument() {
    var_name="$1"
    arg_name="${2:-$1}"

    if [ -z "$(eval echo \\$$var_name)" ]; then
        echo "Error: $arg_name is required" >&2
        exit 1
    fi
}

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
            handle_required_argument name "$2" "$1"
            shift 1;;

        -f|--file)
            handle_required_argument file "$2" "$1"
            shift 1;;

        -l|--log)
            handle_required_argument log "$2" "$1"
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

# Check for required arguments
check_required_argument name "-n/--name"
check_required_argument file "-f/--file"
check_required_argument log "-l/--log"

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
