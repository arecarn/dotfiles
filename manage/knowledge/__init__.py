"""Agent knowledge: which OKF bundles apply here, and how agents read them.

Detailed reference material lives in OKF bundles rather than in the generated
instruction files, so an agent is told what knowledge exists and reads only the
parts a task needs. This package is the one place that decides which bundles
apply; every harness adapter calls it rather than re-implementing activation.

- `config` -- compose `bundles.yaml` with a `dotfiles_local` `bundles_local.yaml`.
- `activation` -- which configured bundles apply here, and the project bundle.
- `okf` -- reading just enough of a bundle to discover and disclose it.
- `resolver` -- the catalog to disclose, one document read, local status.
- `cli` -- the `agent-knowledge` command every adapter shells out to.
- `hooks` -- Claude Code's SessionStart entry point.

The decisions behind the shape of this package are in
docs/adr/0005-resolve-agent-knowledge-once-in-a-shared-cli.md.
"""
