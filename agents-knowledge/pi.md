---
type: Reference
title: Pi configuration
description: What lives in pi/.pi/agent/, how packages are declared, and why stow pre-creates the extensions directory
---
# Layout

`pi/.pi/agent/` holds pi's generated `AGENTS.md` and `extensions/` (TypeScript,
linted and type-checked by `inv lint`).

# Packages

Declared with a `pi_package:` key in `plugins.yaml` and written into pi's own
`~/.pi/agent/settings.json` by `inv pi-setup`, so the preferences pi writes
there stay out of this repo.

A package that reads its own config file gets it here too, as
`extensions/<package>/config.json`. That directory is also where the package
installer clones and writes, so `stow` pre-creates it to keep dploy from
folding it into a symlink.

# What pi does not ship

No MCP or subagent support, by design; both come from third-party packages.
Skills arrive via the shared hub fan-out, not the package.
