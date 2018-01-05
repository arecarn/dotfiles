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
    grep -i copyright >/dev/null 2>&1 "${file}" || continue

    if ! grep -i -e "copyright.*${year}" "${file}" >/dev/null 2>&1; then
        missing_copyright_files="${missing_copyright_files} ${file}"
    fi
done

if [ -n "${missing_copyright_files}" ]; then
    echo "pre-commit: Aborting commit due to missing or incorrect year in copyright notices"
    echo "pre-commit: ${year} is missing in the copyright notice of the following files:"
    for file in ${missing_copyright_files}; do
        printf '    %s\n' "${file}"
    done
    exit 1
fi
