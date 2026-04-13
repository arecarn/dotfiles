### Docker + Makefile Pattern

Projects should use Docker for reproducible environments with these conventions:

**Docker image consistency between local dev and CI:**

Hardcode the image in both `docker-compose.yaml` and `.gitlab-ci.yml`, with a CI job to verify they stay in sync:

```yaml
# docker-compose.yaml
# NOTE: Keep image in sync with .gitlab-ci.yml (verified by image_sync_check job)
services:
  build:
    image: ecoe-dtr.artifactory.blueorigin.com/blue/ngav-build:2026.2.3
```

```yaml
# .gitlab-ci.yml
# NOTE: Keep image in sync with docker-compose.yaml (verified by image_sync_check job)
default:
  image: ecoe-dtr.artifactory.blueorigin.com/blue/ngav-build:2026.2.3

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

**Container detection and conditional execution:**
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

**Wrap make targets with the macro:**
```make
format-check:
    $(call run_in_container,uv run ruff format --check .)

lint-check:
    $(call run_in_container,uv run ruff check .)
```

**Provide a shell target for interactive use:**
```make
shell:
    $(RUN_DOCKER)
```

This pattern allows:
- `make format-check` locally runs in Docker
- CI runs `make format-check` inside the CI container (skips nested Docker)
