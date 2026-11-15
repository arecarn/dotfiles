# shellcheck shell=bash
# Run Paseo's Electron capture harness under a virtual display and save its
# screenshots. Run from the Paseo checkout root, after paseo-install and the
# Electron binary fetch described in README.md. Rebuilds packages/desktop's
# main process first, because the harness loads packages/desktop/dist.
# Output dir defaults to /tmp/paseo-desktop-capture (override with
# PASEO_CAPTURE_HARNESS_OUT_DIR). Mutates only that dir and packages/desktop/dist.
#
# Workarounds, each for one host condition:
#   ELECTRON_DISABLE_SANDBOX=1  npm's Electron has no setuid chrome-sandbox,
#                               so it aborts with SIGTRAP otherwise.
#   --ozone-platform=x11        a Wayland session leaves WAYLAND_DISPLAY set and
#                               Electron picks Wayland, which Xvfb cannot serve.
#   --disable-gpu               with the GPU path every capturePage times out.

[ -f packages/desktop/capture-harness/main.js ] || {
  echo "paseo-desktop-capture: run from the Paseo checkout root" >&2
  exit 1
}

out=${PASEO_CAPTURE_HARNESS_OUT_DIR:-/tmp/paseo-desktop-capture}
mkdir -p "$out"
npm --prefix packages/desktop run build:main

# The harness idles 75 s per state by default (PASEO_CAPTURE_HARNESS_SOAK_MS in
# its main.js); screenshots do not need the soak, so default to 1 s.
env -u WAYLAND_DISPLAY \
  ELECTRON_DISABLE_SANDBOX=1 \
  PASEO_CAPTURE_HARNESS_SOAK_MS="${PASEO_CAPTURE_HARNESS_SOAK_MS:-1000}" \
  PASEO_CAPTURE_HARNESS_OUT_DIR="$out" \
  xvfb-run -a -s "-screen 0 1280x800x24" \
  node_modules/.bin/electron --disable-gpu --ozone-platform=x11 \
  packages/desktop/capture-harness/main.js
echo "screenshots in $out"
