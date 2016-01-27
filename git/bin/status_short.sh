source ~/dotfiles/git/bin/correct_path.sh
git status --short --branch "$@" && git --no-pager stash-list-pretty
