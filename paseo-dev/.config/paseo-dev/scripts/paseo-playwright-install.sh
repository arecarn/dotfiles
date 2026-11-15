# shellcheck shell=bash
# Install the Chromium that the checkout's own pinned Playwright expects. Run
# from the checkout root, after paseo-install. Nix does not provide the browser,
# so it can never go stale against package-lock.json.
#
# Requires ./node_modules/.bin/playwright (exits 1 with a message if absent) and
# network access. Writes only Playwright's browser cache (~/.cache/ms-playwright
# unless PLAYWRIGHT_BROWSERS_PATH says otherwise). Safe to repeat. Prints the
# installed Playwright version on success; exits non-zero on any install failure.
#
# Playwright refuses to install on a distro release it does not know yet (1.58
# on Ubuntu 26.04: "does not support chromium on ubuntu26.04-x64"). The Ubuntu
# 24.04 build runs there, so retry with that platform. Only the install needs
# the override; launching the installed browser works without it.

[ -x node_modules/.bin/playwright ] || {
  echo "paseo-playwright-install: run paseo-install first, from the Paseo checkout root" >&2
  exit 1
}

if ! out=$(npx playwright install chromium 2>&1); then
  if grep -q "does not support chromium" <<<"$out"; then
    echo "paseo-playwright-install: host not supported by this Playwright, using the ubuntu24.04-x64 build" >&2
    PLAYWRIGHT_HOST_PLATFORM_OVERRIDE=ubuntu24.04-x64 npx playwright install chromium
  else
    echo "$out" >&2
    exit 1
  fi
fi
npx playwright --version
