"""Facts about this checkout and the machine it is on.

Shared by `tasks.py` and the modules under `manage`, so each is defined once.
"""

import os
import pathlib

# This file is `<repo>/manage/repo.py`, so the root is two levels up. Derived
# rather than assumed from the working directory: `StowPlan.clean` decides whether
# a symlink points into this repo by comparing against it, and a wrong answer
# there means either skipping dead links or deleting live ones.
ROOT = pathlib.Path(__file__).resolve().parent.parent

IS_WINDOWS = os.name == "nt"

# Skipped when walking the checkout or the home directory: large, generated, or
# not ours to touch.
# `.claude` and `.worktrees` hold agent worktrees -- whole checkouts of this repo
# at another revision. Walking one lints a different commit's files as if they
# were this one's, which fails on code that is correct in both. It also feeds
# pylint two copies of every shared module, so its duplicate-code check reports
# R0801 against whichever file it happens to name first -- a failure that looks
# like it belongs to the file it blames.
# The TypeScript names here mirror the "exclude" list in tsconfig.json; change
# both together, or lint_typescript's guard and tsc's input set diverge.
EXCLUDE_DIRS = {
    ".venv",
    ".git",
    ".claude",
    ".worktrees",
    "__pycache__",
    ".cache",
    "node_modules",
    ".superpowers",
}
