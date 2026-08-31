---
type: Playbook
title: Docker and Makefile pattern
description: The compose/Makefile/CI templates for a project whose make targets run inside a container, including keeping one image pinned in two files and detecting that you are already in a container
---
# What this pattern gives you

`make format-check` runs inside the container locally, and runs directly inside
CI's own container without nesting Docker. One image, pinned in two files, with
a job that fails when they drift.

# Pinning one image in two files

Hardcode the image in both `docker-compose.yaml` and `.gitlab-ci.yml`, with a CI job to verify they stay in sync:

```yaml
# docker-compose.yaml
# NOTE: Keep image in sync with .gitlab-ci.yml (verified by image_sync_check job)
services:
  build:
    image: registry.example.com/org/build-image:2026.2.3
```

```yaml
# .gitlab-ci.yml
# NOTE: Keep image in sync with docker-compose.yaml (verified by image_sync_check job)
default:
  image: registry.example.com/org/build-image:2026.2.3

image_sync_check:
  stage: check
  script:
    - make image-sync-check
```

```make
# makefile
.PHONY: image-sync-check
image-sync-check:  ## Check docker-compose.yaml image matches .gitlab-ci.yml
	@DC_IMAGE=$$(grep -oP 'image:\s*\K\S+' docker-compose.yaml | head -1); \
	CI_IMAGE=$$(grep -oP '^\s+image:\s+\K\S+' .gitlab-ci.yml | head -1); \
	if [ "$$DC_IMAGE" != "$$CI_IMAGE" ]; then \
		echo "ERROR: Docker image mismatch!"; exit 1; \
	fi; \
	echo "Images are in sync."
```

# Detecting that you are already in a container
```make
export UID := $(shell id -u)
export GID := $(shell id -g)

RUN_DOCKER = docker compose run --rm service-name

# Detect if already running in a container
ifeq (, $(shell egrep '(docker|containerd)' /proc/self/cgroup 2> /dev/null))
    USE_DOCKER := 1
else
    USE_DOCKER := 0
endif

# Macro to conditionally wrap commands
ifneq ($(USE_DOCKER),0)
    define run_in_container
        $(RUN_DOCKER) bash -c '$(1)'
    endef
else
    define run_in_container
        $(1)
    endef
endif
```

# Wrapping the targets
```make
format-check:
    $(call run_in_container,uv run ruff format --check .)

lint-check:
    $(call run_in_container,uv run ruff check .)
```

# A shell for interactive use
```make
shell:
    $(RUN_DOCKER)
```
