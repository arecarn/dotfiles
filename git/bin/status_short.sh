source ~/dotfiles/git/bin/correct_path.sh

# Note if a rebase is in Progress
YELLOW='\033[1;33m'
NC='\033[0m' # No Color
ls `git rev-parse --git-dir` |  grep "rebase" --silent && printf "${YELLOW}NOTE:${NC} Rebase In Progress\n"

git status --short --branch "$@" && git --no-pager stash-list-pretty
