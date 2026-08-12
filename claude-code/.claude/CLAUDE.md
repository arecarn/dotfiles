# Project Instructions

## General Project Guidelines

@references/build-ci.md
@references/docker-makefile.md
@references/merge-requests.md
@references/output-formatting.md
@references/python.md
@references/teams.md

## Local

Private and work-specific instructions live in a `dotfiles_local` repo, which
stows its own reference files into the same `~/.claude/references/`. This repo
imports that config through one stable filename and never names its contents, so
nothing private is recorded here. A missing import is ignored silently, so this
file also works standalone when no `dotfiles_local` is checked out.

@references/local.md
