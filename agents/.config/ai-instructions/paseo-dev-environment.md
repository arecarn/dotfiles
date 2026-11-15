### Paseo Development Environment

In a Paseo checkout, the toolchain comes from a personal Nix flake that direnv
activates per checkout. Set one up with
`bash ~/.config/paseo-dev/scripts/paseo-dev-activate.sh` (the script is not on
PATH). It writes an `.envrc` that also unsets `PASEO_HOME`, so the dev stack
uses the checkout-local home. First-time install sequence:
`~/.config/paseo-dev/README.md`.

- **Run commands inside it non-interactively** with `direnv exec . <command>`
  (or `nix develop path:$HOME/.config/paseo-dev -c <command>`); do not rely on
  an interactive shell hook.
- **Run commits, pushes and the GitHub CLI on the host.** No credentials are
  inside the environment.
- **It does not provide iOS builds or isolation.** Commands still run on the
  host with full access.
- `paseo-dev-check` warns about missing prerequisites (virtualization, file
  watcher limit) and drift of Node and Playwright from the checkout's own pins.
