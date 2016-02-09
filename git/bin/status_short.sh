source ~/dotfiles/git/bin/correct_path.sh

YELLOW='\033[1;33m'
NC='\033[0m' # No Color

if git rev-parse; then # if we are in a git repo
    # notify when a rebase is in progress
    if ls `git rev-parse --git-dir` | grep "rebase" --silent; then
        printf "${YELLOW}Rebase In Progress\n"
    fi
    git status --short --branch "$@"
    git --no-pager stash-list-pretty
fi
