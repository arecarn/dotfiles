#!/bin/sh

#
# Git pre-commit hook to check for bad white spaces
#

# Check if this is the initial commit
if git rev-parse --verify HEAD >/dev/null 2>&1; then
    against=HEAD
else
    against=4b825dc642cb6eb9a060e54bf8d69288fbee4904
fi

# Use git diff-index to check for white space errors
if ! git diff-index --check --cached ${against}; then
    echo "pre-commit: Aborting commit due to white space errors"
    exit 1
fi
