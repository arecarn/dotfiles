---
type: Playbook
title: Docker and Makefile pattern
description: Generic single-container dispatch for all Make goals, direct execution in CI, linked-worktree mounts, and keeping one build image pinned across Compose and CI
---
## What this pattern gives you

Every local Make invocation enters one build container. Multiple requested goals
and their dependency graphs share that container. CI, which already runs in the
build image, executes the same targets directly without nesting Docker.

```text
Host: make lint-check test
  -> docker compose run --rm build "make lint-check test"

CI/container: make lint-check test
  -> run both recipes directly
```

Adding a target requires only its ordinary recipe. Container dispatch remains
centralized rather than repeated around every target.

## Generic Make dispatcher

Keep the host dispatcher and the real target graph in one Makefile:

```make
SHELL := /bin/bash

export EXPORT_UID := $(shell id -u)
export EXPORT_GID := $(shell id -g)
# A linked worktree's .git file points into this directory outside PWD.
export GIT_COMMON_DIR := $(shell git rev-parse --path-format=absolute --git-common-dir)

RUN_DOCKER := docker compose run --rm build
IN_CONTAINER := $(shell test -f /.dockerenv && echo 1 || \
	grep -qE '(docker|containerd)' /proc/self/cgroup 2>/dev/null && echo 1)

.DEFAULT_GOAL := help

ifeq ($(IN_CONTAINER),)
    REQUESTED_GOALS := $(if $(MAKECMDGOALS),$(MAKECMDGOALS),$(.DEFAULT_GOAL))

    # MAKEOVERRIDES preserves command-line assignments and their escaping.
    CONTAINER_MAKE_ARGUMENTS := $(strip $(MAKEOVERRIDES) IN_CONTAINER=1 $(REQUESTED_GOALS))

    .PHONY: __container_dispatch $(REQUESTED_GOALS)
    $(REQUESTED_GOALS): __container_dispatch ;

    __container_dispatch:
	$(RUN_DOCKER) "make $(CONTAINER_MAKE_ARGUMENTS)"
else
.PHONY: help
help: ## Show available targets
	@grep -E '^[a-zA-Z0-9_.%-]+:.*?## .*$$' $(MAKEFILE_LIST)

.PHONY: check
check: lint-check format-check test ## Run all checks

.PHONY: lint-check
lint-check: ## Check linting
	uv run ruff check .

.PHONY: format-check
format-check: ## Check formatting
	uv run ruff format --check .

.PHONY: test
test: ## Run tests
	uv run pytest

.PHONY: shell
shell: ## Open a shell in the build container
	/bin/bash
endif
```

The semicolon-only rules make each requested host goal depend on one shared
`__container_dispatch` target. Make runs that prerequisite once, even when the
user requests several goals. The real dependency graph is parsed only inside the
container.

`MAKEOVERRIDES` is Make's built-in representation of command-line variable
assignments. Prefer it to scanning `.VARIABLES`: it preserves Make's escaping,
and appending `IN_CONTAINER=1` ensures the inner invocation takes the direct
execution path even if the outer invocation overrode that variable.

## Linked worktrees

Mount both the working tree and Git's common directory. Mounting only `${PWD}`
works in a normal checkout but breaks Git commands in a linked worktree because
its `.git` file points into the primary checkout.

```yaml
services:
  build:
    image: registry.example.com/org/build-image:2026.2.3
    working_dir: ${PWD}
    volumes:
      - ${PWD}:${PWD}
      - ${GIT_COMMON_DIR}:${GIT_COMMON_DIR}
```

The common-directory mount is read/write by default. Use `:ro` only when no
containerized target needs to modify Git metadata.

## Pinning one image in two files

Hardcode the image in both `docker-compose.yaml` and `.gitlab-ci.yml`, with a CI
job that verifies they stay in sync:

```yaml
# docker-compose.yaml
# NOTE: Keep image in sync with .gitlab-ci.yml (verified by image-sync-check)
services:
  build:
    image: registry.example.com/org/build-image:2026.2.3
```

```yaml
# .gitlab-ci.yml
# NOTE: Keep image in sync with docker-compose.yaml (verified by image-sync-check)
default:
  image: registry.example.com/org/build-image:2026.2.3

image-sync-check:
  stage: check
  script:
    - make image-sync-check
```

```make
.PHONY: image-sync-check
image-sync-check: ## Check Docker Compose and CI use the same image
	@DC_IMAGE=$$(grep -oP 'image:\s*\K\S+' docker-compose.yaml | head -1); \
	CI_IMAGE=$$(grep -oP '^\s+image:\s+\K\S+' .gitlab-ci.yml | head -1); \
	if [ "$$DC_IMAGE" != "$$CI_IMAGE" ]; then \
		echo "ERROR: Docker image mismatch!"; exit 1; \
	fi; \
	echo "Images are in sync."
```

## Behavioral checks

Test the dispatch boundary rather than timing, which varies with image pulls and
package caches:

- Every standalone host goal starts exactly one container.
- Several host goals share one container and preserve their order.
- An invocation without goals forwards the default goal.
- Command-line Make variables reach the inner invocation.
- Container-mode aggregate targets execute every dependency directly.
- Container-mode `shell` opens Bash without invoking Docker.
- `GIT_COMMON_DIR` is absolute so linked-worktree Git commands work.
