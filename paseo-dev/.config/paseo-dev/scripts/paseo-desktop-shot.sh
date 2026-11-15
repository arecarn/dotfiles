# shellcheck shell=bash
# Screenshot the real Paseo desktop app (the `npm run dev:desktop` stack:
# Metro plus Electron) on a virtual display. Run from the Paseo checkout root
# after paseo-install and the Electron binary fetch described in README.md.
# Writes the root window of the virtual display to a PNG, prints its mean pixel
# value (0 is black, 1 is white) and exits non-zero if the window stays black.
#
# Environment:
#   PASEO_DESKTOP_SHOT_OUT      PNG path (default /tmp/paseo-desktop-shot.png)
#   PASEO_DESKTOP_SHOT_TIMEOUT  seconds to wait for a non-black frame (default
#                               600; the first Metro web bundle of a checkout
#                               takes minutes, later runs about a minute)
#   EXPO_PORT, PASEO_LISTEN     passed through to the dev stack; set both to
#                               ports other than 6768/8081 to run beside
#                               another dev stack
# Mutates packages/desktop/dist, .dev/ in the checkout, and the PNG. The stack
# is stopped on exit. PASEO_HOME is unset so the stack uses the checkout-local
# .dev/paseo-home, never the real daemon's state.
#
# The first exec is the workaround this script exists for: Electron 44 picks
# Wayland from XDG_SESSION_TYPE=wayland even when WAYLAND_DISPLAY is unset, so
# the window never reaches Xvfb. A --ozone-platform flag set from the app's
# JavaScript (PASEO_ELECTRON_FLAGS) is too late for the browser process, so the
# session variable has to be gone before Electron starts. See
# docs/gotchas/electron-desktop-stays-black-under-xvfb-on-a-wayland-session.md.

if [ -z "${PASEO_DESKTOP_SHOT_INNER:-}" ]; then
  [ -f packages/desktop/scripts/dev.sh ] || {
    echo "paseo-desktop-shot: run from the Paseo checkout root" >&2
    exit 1
  }
  exec env -u WAYLAND_DISPLAY -u XDG_SESSION_TYPE -u PASEO_HOME \
    PASEO_DESKTOP_SHOT_INNER=1 \
    xvfb-run -a -s "-screen 0 1280x800x24" "$0"
fi

out=${PASEO_DESKTOP_SHOT_OUT:-/tmp/paseo-desktop-shot.png}
timeout_s=${PASEO_DESKTOP_SHOT_TIMEOUT:-600}
log=${out%.png}.log
home=$PWD/.dev/paseo-home

# A fresh process group, so one kill stops Metro, Electron and their children.
setsid bash packages/desktop/scripts/dev.sh >"$log" 2>&1 &
stack=$!

# The app also starts a detached, desktop-managed daemon and a terminal worker
# in the checkout-local home. They outlive the process group, so stop them by
# the pid file and the checkout-local home path, so a real daemon is never hit.
# shellcheck disable=SC2329  # invoked through the EXIT trap
stop_stack() {
  # Every step may fail (already gone); errexit must not end the cleanup.
  kill -TERM -- "-$stack" 2>/dev/null || true
  sleep 3
  kill -KILL -- "-$stack" 2>/dev/null || true
  daemon_pid=$(sed -n 's/.*"pid":\([0-9]*\).*/\1/p' "$home/paseo.pid" 2>/dev/null || true)
  [ -z "$daemon_pid" ] || kill "$daemon_pid" 2>/dev/null || true
  pkill -f -- "--paseo-home $home" 2>/dev/null || true
  # The daemon renames its process; match it by name and this checkout's cwd so
  # a daemon of another checkout, or the real one, is never touched.
  for pid in $(pgrep -x "Paseo Daemon" || true); do
    if [ "$(readlink "/proc/$pid/cwd")" = "$PWD" ]; then kill "$pid" 2>/dev/null || true; fi
  done
}
trap stop_stack EXIT

mean=0
waited=0
while [ "$waited" -lt "$timeout_s" ]; do
  sleep 5
  waited=$((waited + 5))
  xwd -root -display "$DISPLAY" | magick xwd:- "$out" 2>/dev/null || continue
  mean=$(magick "$out" -format '%[fx:mean]' info:)
  # The app's own background is dark but not black (about 0.1), so 0.02 only
  # trips on a black frame.
  if awk -v m="$mean" 'BEGIN { exit !(m > 0.02) }'; then
    # Let the first route finish drawing, then keep that frame.
    sleep 5
    xwd -root -display "$DISPLAY" | magick xwd:- "$out"
    mean=$(magick "$out" -format '%[fx:mean]' info:)
    echo "screenshot: $out mean=$mean after ${waited}s (stack log: $log)"
    exit 0
  fi
done
echo "paseo-desktop-shot: still black after ${timeout_s}s, mean=$mean (stack log: $log)" >&2
exit 1
