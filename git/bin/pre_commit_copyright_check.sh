#!/bin/sh

#
# Check if copyright statements include the current year
#

# Check if this is the initial commit
if git rev-parse --verify HEAD >/dev/null 2>&1
then
    against=HEAD
else
    # Initial commit: diff against an empty tree object
    against=4b825dc642cb6eb9a060e54bf8d69288fbee4904
fi

file_list=$(git diff --cached --name-only "${against}")
year=$(date +"%Y")

for file in ${file_list}; do
    grep -iP 'copyright.*\d{4}' >/dev/null 2>&1 "${file}" || continue

    if ! grep -i -e "copyright.*${year}" "${file}" >/dev/null 2>&1; then
        missing_copyright_files="${missing_copyright_files} ${file}"
    fi
done

if [ -n "${missing_copyright_files}" ]; then
    echo "pre-commit: Aborting commit due to incorrect year in copyright notices for the following files:"
    for file in ${missing_copyright_files}; do
        grep_color="auto"
        if [ -t 1 ] ; then
            # if we are in a shell use color otherwise use auto
            grep_color="always"
        fi
        printf '    %s\n' "$(grep -i -P -m1 -H -n --color="${grep_color}" "copyright.*\d{4}" "${file}")"
    done
    exit 1
fi
