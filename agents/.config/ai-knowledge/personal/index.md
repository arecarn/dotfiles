---
okf_version: "0.2"
---
# Personal knowledge

Reference material that applies to my work in any repository. Read an entry when
its description matches the task; these are patterns and procedures, not
instructions.

# Project scaffolding

* [Docker and Makefile pattern](docker-makefile.md) - Read when setting up or changing a Makefile, Dockerfile, build container, or CI config: the task-runner and CI conventions, single-container Make dispatch, linked-worktree mounts, one pinned build image, standard target names, and the self-documenting `help` pattern

* [Python project tooling](python-tooling.md) - Read when starting or changing a Python project: the preferred tools for package management, linting and formatting, and type checking

# Writing for review

* [Showing authored prose for review](posting-authored-prose.md) - Read before posting or editing prose under my name in Jira, merge requests, wikis, email, or tasks: how to show an edit as a diff, reference boilerplate instead of reproducing it, and present a batch whole

* [Change request descriptions and review replies](change-requests.md) - Read
  when writing or editing a merge request or pull request description, or
  replying that review feedback was addressed: the final-diff rule, the
  Verification section, preserving templates, and naming the commit SHA

# Agent workspaces

* [Paseo workspace and agent orchestration](paseo.md) - prefers Paseo for
  worktrees/agent orchestration; CLI syntax for running agents into worktrees,
  the --provider requirement, the branch-name-collision gotcha, and that its
  GitHub/GitLab integration needs gh or glab installed and authenticated
  since Paseo has no auth of its own
