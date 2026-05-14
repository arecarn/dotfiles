#!/bin/bash

#
# Git pre-commit hook to check for missing shebang in non-binary executable
# files
#

# Check if this is the initial commit
if git rev-parse --verify HEAD >/dev/null 2>&1
then
    against=HEAD
else
    # Initial commit: diff against an empty tree object
    against=4b825dc642cb6eb9a060e54bf8d69288fbee4904
fi

missing_shebang_files=()
while IFS= read -r -d '' file; do
    if [ -x "${file}" ]; then
        if ! file -bL --mime "${file}" | grep -q 'binary'; then
            if [ ! "$(git show :"${file}" | head -c 2)" = "#!" ]; then
                missing_shebang_files+=("${file}")
            fi
        fi
    fi
done < <(git diff --cached --name-only -z "${against}")

if [ ${#missing_shebang_files[@]} -gt 0 ]; then
    echo "pre-commit: Aborting commit due to missing shebang in the following non-binary"
    echo "executable files:"
    for file in "${missing_shebang_files[@]}"; do
        printf '    %s\n' "${file}"
    done
    exit 1
fi
