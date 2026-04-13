### Build & CI Structure

- Projects should have a `Makefile` and CI configuration files
- CI pipelines should only call `make` targets (keeps CI simple and reproducible locally)

### Standard Make Targets

| Target | Purpose |
|--------|---------|
| `help` | Print available targets with descriptions |
| `lint` | Run linters and fix issues |
| `lint-check` | Run linters without fixing (for CI) |
| `format` | Format code |
| `format-check` | Check formatting without modifying (for CI) |

### Self-Documenting Help Pattern

Use `## ` comments after target names to enable auto-generated help:

```make
.PHONY: lint
lint: ## Run all static analysis
lint: check spell

.PHONY: clean
clean: ## Remove build artifacts
	rm -rf dist/

help: ## Print this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
```

Running `make help` outputs:
```
clean                          Remove build artifacts
help                           Print this help
lint                           Run all static analysis
```

Reference: [marmelab.com/blog/2016/02/29/auto-documented-makefile.html](https://marmelab.com/blog/2016/02/29/auto-documented-makefile.html)
