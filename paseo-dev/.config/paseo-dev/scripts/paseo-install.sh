# shellcheck shell=bash
# Install a Paseo checkout's dependencies. Run from the checkout root.
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
