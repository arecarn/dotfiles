#!/bin/sh

#
# Git pre-commit hook to check if copyright statements include the current year
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
    git show :"${file}" | grep -iP 'copyright.*\d{4}' >/dev/null 2>&1 || continue

    if ! git show :"${file}" | grep -i -e "copyright.*${year}" >/dev/null 2>&1; then
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
        printf '    %s:%s\n' ${file} "$(git show :${file} | grep -i -P -m1 -n --color="${grep_color}" "copyright.*\d{4}")"
    done
    exit 1
fi
