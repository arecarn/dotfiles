#!/bin/sh

# This script ensures that the relative file path is used for aliases that
# include a "!" at the start, otherwise they are run at the root of the
# repository.
#
# Note GIT_PREFIX is empty at repository root

if [ -n "$GIT_PREFIX" ]; then
    cd "$GIT_PREFIX" || return 1;
fi
