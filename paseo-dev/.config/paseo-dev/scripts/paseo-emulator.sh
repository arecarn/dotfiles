# shellcheck shell=bash
# paseo-emulator start|stop|status: a headless Android emulator for the android
# shell. Needs ANDROID_PLATFORM, ANDROID_SYSTEM_IMAGE_TYPE and ANDROID_ABI from
# the flake (the one place those versions are defined) and the SDK tools on PATH.
#
# start creates the AVD if missing, boots it with no window, no audio and
# software rendering, and returns once adb reports the boot finished. It is
# idempotent. stop ends the emulator this helper started.
#
# All state lives under XDG directories, never in a checkout: the AVD and the
# adb keys under $XDG_DATA_HOME/paseo-dev/android, the pid and log under
# $XDG_STATE_HOME/paseo-dev. Overrides for tests: PASEO_DEV_KVM_DEVICE,
# PASEO_EMULATOR_BOOT_TIMEOUT (seconds), PASEO_EMULATOR_POLL_SECONDS,
# PASEO_EMULATOR_PORT.
platform=${ANDROID_PLATFORM:?run inside the android shell}
image_type=${ANDROID_SYSTEM_IMAGE_TYPE:?run inside the android shell}
abi=${ANDROID_ABI:?run inside the android shell}

data=${XDG_DATA_HOME:-$HOME/.local/share}/paseo-dev/android
state=${XDG_STATE_HOME:-$HOME/.local/state}/paseo-dev
# Where the Android tools look for the AVD and for adb's keys and settings.
export ANDROID_USER_HOME=$data
export ANDROID_EMULATOR_HOME=$data/emulator
export ANDROID_AVD_HOME=$data/avd
avd=paseo-dev-android-$platform
image="system-images;android-$platform;$image_type;$abi"
pidfile=$state/emulator.pid
log=$state/emulator.log
port=${PASEO_EMULATOR_PORT:-5554}
serial=emulator-$port
timeout=${PASEO_EMULATOR_BOOT_TIMEOUT:-300}
poll=${PASEO_EMULATOR_POLL_SECONDS:-2}

running() {
  [ -s "$pidfile" ] && kill -0 "$(cat "$pidfile")" 2>/dev/null
}

start() {
  if running; then
    echo "emulator already running ($serial)"
    return 0
  fi
  local kvm=${PASEO_DEV_KVM_DEVICE:-/dev/kvm}
  if ! [ -r "$kvm" ] || ! [ -w "$kvm" ]; then
    echo "kvm: $kvm is not usable; join the kvm group (sudo usermod -aG kvm \$USER) and log in again" >&2
    return 1
  fi
  mkdir -p "$ANDROID_AVD_HOME" "$ANDROID_EMULATOR_HOME" "$state"
  if [ ! -d "$ANDROID_AVD_HOME/$avd.avd" ]; then
    echo "creating AVD $avd from $image"
    echo no | avdmanager create avd -n "$avd" -k "$image" >/dev/null
  fi
  # Start the adb server explicitly, with its output detached, rather than
  # letting the first adb call below fork it.
  adb start-server >/dev/null 2>&1 </dev/null
  : >"$log"
  # setsid detaches the emulator from this shell so it outlives the helper.
  setsid emulator -avd "$avd" -port "$port" -no-window -no-audio -no-boot-anim \
    -no-snapshot -no-metrics -gpu swiftshader_indirect >"$log" 2>&1 </dev/null &
  echo $! >"$pidfile"

  echo "waiting for $serial to boot (up to ${timeout}s)"
  local waited=0
  while true; do
    if ! running; then
      echo "emulator exited before boot finished; log:" >&2
      cat "$log" >&2
      rm -f "$pidfile"
      return 1
    fi
    if [ "$(adb -s "$serial" shell getprop sys.boot_completed 2>/dev/null | tr -d '\r')" = 1 ]; then
      echo "booted: $serial"
      return 0
    fi
    sleep "$poll"
    waited=$(awk -v w="$waited" -v p="$poll" 'BEGIN { print w + p }')
    if awk -v w="$waited" -v t="$timeout" 'BEGIN { exit !(w >= t) }'; then
      echo "timed out after ${timeout}s waiting for boot; log: $log" >&2
      return 1
    fi
  done
}

stop() {
  if ! running; then
    rm -f "$pidfile"
    echo "emulator not running"
    return 0
  fi
  local pid
  pid=$(cat "$pidfile")
  adb -s "$serial" emu kill >/dev/null 2>&1 || true
  kill "$pid" 2>/dev/null || true
  for _ in $(seq 1 50); do
    kill -0 "$pid" 2>/dev/null || break
    sleep 0.2
  done
  kill -9 "$pid" 2>/dev/null || true
  rm -f "$pidfile"
  echo "emulator stopped"
}

case "${1:-}" in
  start) start ;;
  stop) stop ;;
  status)
    if running; then echo "running ($serial)"; else echo "not running"; fi ;;
  *)
    echo "usage: paseo-emulator start|stop|status" >&2
    exit 2 ;;
esac
