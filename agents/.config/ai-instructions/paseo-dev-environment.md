### Paseo Development Environment

In a Paseo checkout, the toolchain comes from a personal Nix flake that direnv
activates per checkout (`paseo-dev-activate` sets one up).

- **Run commands inside it non-interactively** with `direnv exec . <command>`
  (or `nix develop path:$HOME/.config/paseo-dev -c <command>`); do not rely on
  an interactive shell hook.
- **Run commits, pushes and the GitHub CLI on the host.** No credentials are
  inside the environment.
- **It does not provide iOS builds or isolation.** Commands still run on the
  host with full access.
- `paseo-dev-check` warns about missing prerequisites (virtualization, file
  watcher limit) and Node or Playwright drift.
