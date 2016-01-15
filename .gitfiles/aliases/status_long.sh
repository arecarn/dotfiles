source ~/dotfiles/.gitfiles/aliases/correct_path.sh
git status "$@" &&  printf '\n'; git --no-pager stash-list-pretty --name-status
