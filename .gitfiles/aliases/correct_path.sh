# This script ensures that the relative file path is used for aliases that
# include a "!" at the start, otherwise they are run at the root of the
# repository.
#
# Note GIT_PREFIX is empty at repository root

test -n "$GIT_PREFIX" && cd $GIT_PREFIX;
