#!/bin/sh

# Git pre-push hook to run linters on the dotfiles repo.
# Only runs when pushing from a directory that contains a tasks.py with
# an invoke lint task (i.e., the dotfiles repo).

if [ ! -f "tasks.py" ] || ! grep -q "def lint" tasks.py 2>/dev/null; then
    exit 0
fi

if ! command -v uv >/dev/null 2>&1; then
    echo "pre-push: uv not found, skipping lint check"
    exit 0
fi

echo "pre-push: running linters..."
if ! uv run invoke lint; then
    echo "pre-push: lint failed — fix issues before pushing"
    return_code=1
else
    echo "pre-push: lint passed"
    return_code=0
fi

exit ${return_code}
