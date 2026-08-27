"""Agent knowledge: which OKF bundles apply here, and how agents read them.

Detailed reference material lives in OKF bundles rather than in the generated
instruction files, so an agent is told what knowledge exists and reads only the
parts a task needs. This package is the one place that decides which bundles
apply; every harness adapter calls it rather than re-implementing selection.

- `config` -- compose `bundles.yaml` with a `dotfiles_local` `bundles_local.yaml`.

Design notes and the full requirement list live in the local spec at
`~/okf-agent-integration-spec.md`.
"""
