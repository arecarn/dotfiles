# paseo-dev

A personal Nix flake with the toolchain for developing Paseo. It lives outside
the Paseo repo and changes nothing in it. Stow links this directory to
`~/.config/paseo-dev`.

## First-time setup of a checkout

Run from the Paseo checkout or worktree root:

```sh
bash ~/.config/paseo-dev/scripts/paseo-dev-activate.sh   # .envrc + direnv allow
direnv exec . paseo-install             # npm ci, patches, app-deps and server builds
direnv exec . paseo-playwright-install  # Chromium for the locked Playwright
direnv exec . paseo-dev-check           # warn-only prerequisite and drift report
```

`paseo-install` runs `npm ci --ignore-scripts`, then the patch step with
`node_modules/.bin` on PATH, then `npm run build:app-deps` and
`npm run build:server`. Never install with plain `npm ci --ignore-scripts`: it
skips `patches/` and the app crashes. Scripts stay disabled so no git hook is
installed.

The activation script writes an untracked `.envrc` and excludes it through the
repo's local exclude file. The `.envrc` unsets `PASEO_HOME`, so a value leaking
from the host shell cannot point the dev stack at the real daemon's state; it
uses the checkout-local `.dev/paseo-home`.

## Optional: Electron binary for paseo-desktop-capture

`--ignore-scripts` skips Electron's binary download. Fetch it once per
checkout, then capture:

```sh
direnv exec . node node_modules/electron/install.js
direnv exec . paseo-desktop-capture
```

## Android

`nix develop path:$HOME/.config/paseo-dev#android` adds the SDK, JDK, Gradle and
the emulator. It is only evaluated when asked for. There is no emulator boot
helper yet (open gap).

## Updating the pins

```sh
nix flake update --flake path:$HOME/.config/paseo-dev
git -C <dotfiles checkout> diff -- paseo-dev/.config/paseo-dev/flake.lock
```

Review the lock diff before committing. The Node and Java majors and the
Android versions are defined once at the top of `flake.nix`; the smoke script
(`paseo-dev-smoke`) reads them from the environment.

## Paseo's own worktree setup

A worktree created through Paseo runs its `npm ci` on the host, outside this
environment, so it needs a host Node. Without one, re-run `paseo-install`
inside the environment afterwards.
