# Execute a command at the top level of a Git repository directory while
# taking into account submodules

GIT_TOP="${GIT_DIR%%/.git/modules/*}";
[ ".$GIT_TOP" != ".$GIT_DIR" ] && cd "$GIT_TOP";
exec "$@";

