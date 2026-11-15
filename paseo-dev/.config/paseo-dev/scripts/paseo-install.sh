# shellcheck shell=bash
# First-time setup of a Paseo checkout: install dependencies, apply patches,
# then build the workspace packages the app and daemon load. Run from the
# checkout root; safe to repeat. Does not fetch browsers (see
# paseo-playwright-install) or Electron (see README.md).
#
# Plain `npm ci --ignore-scripts` skips patches/, and the app then crashes
# (SheetHostScope, missing patched exports). The patch step needs the local
# node_modules/.bin on PATH. Scripts stay disabled so the `prepare` script
# never runs `lefthook install` and no git hook is installed.

[ -f scripts/postinstall-patches.mjs ] || {
  echo "paseo-install: run from the Paseo checkout root" >&2
  exit 1
}

npm ci --ignore-scripts
PATH="$PWD/node_modules/.bin:$PATH" node scripts/postinstall-patches.mjs
npm run build:app-deps
npm run build:server
