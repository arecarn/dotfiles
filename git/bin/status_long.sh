source ~/dotfiles/git/bin/correct_path.sh
git status "$@" &&  printf '\n' && git --no-pager stash-list-pretty --name-status
