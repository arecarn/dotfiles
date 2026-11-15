# shellcheck shell=bash
# Behavior tests for paseo-emulator. Stub emulator, avdmanager and adb binaries
# stand in for the SDK so the helper's own logic runs without hardware
# virtualization. Run: bash paseo-emulator.test.sh [path-to-helper]
set -u
here=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
helper=${1:-$here/paseo-emulator.sh}
tmp=$(mktemp -d)
trap 'kill "$(cat "$tmp/state/paseo-dev/emulator.pid" 2>/dev/null)" 2>/dev/null; rm -rf "$tmp"' EXIT

mkdir -p "$tmp/bin" "$tmp/data" "$tmp/state"
touch "$tmp/kvm"

# avdmanager records its call and creates the AVD directory it was asked for.
cat >"$tmp/bin/avdmanager" <<'STUB'
#!/usr/bin/env bash
echo "$*" >>"$STUB_LOG/avdmanager"
name=
while [ $# -gt 0 ]; do [ "$1" = -n ] && name=$2; shift; done
mkdir -p "$ANDROID_AVD_HOME/$name.avd"
STUB
# emulator records its arguments and stays up like the real one.
cat >"$tmp/bin/emulator" <<'STUB'
#!/usr/bin/env bash
echo "$*" >>"$STUB_LOG/emulator"
[ -n "${STUB_EMULATOR_FAILS:-}" ] && { echo "emulator exploded" >&2; exit 1; }
exec sleep 300
STUB
# adb reports boot completion after STUB_BOOT_AFTER polls (never if unset).
cat >"$tmp/bin/adb" <<'STUB'
#!/usr/bin/env bash
case "$*" in
  *getprop*)
    n=$(cat "$STUB_LOG/polls" 2>/dev/null || echo 0)
    echo $((n + 1)) >"$STUB_LOG/polls"
    if [ -n "${STUB_BOOT_AFTER:-}" ] && [ "$n" -ge "$STUB_BOOT_AFTER" ]; then echo 1; else echo; fi ;;
  *devices*) printf 'List of devices attached\nemulator-5554\tdevice\n' ;;
esac
exit 0
STUB
chmod +x "$tmp/bin/"*

run() {
  out=$(env \
    PATH="$tmp/bin:$PATH" \
    STUB_LOG="$tmp" \
    XDG_DATA_HOME="$tmp/data" XDG_STATE_HOME="$tmp/state" \
    HOME="$tmp/home" \
    ANDROID_PLATFORM=35 ANDROID_SYSTEM_IMAGE_TYPE=google_apis ANDROID_ABI=x86_64 \
    PASEO_DEV_KVM_DEVICE="$tmp/kvm" \
    PASEO_EMULATOR_BOOT_TIMEOUT=5 PASEO_EMULATOR_POLL_SECONDS=0.1 \
    "$@" bash "$helper" "$cmd" 2>&1)
  status=$?
}

fails=0
# ok_if <what> <command...>: pass when the command succeeds.
ok_if() {
  local what=$1
  shift
  if "$@"; then
    echo "ok   $what"
  else
    echo "FAIL $what"
    fails=1
  fi
}
expect() {
  local what=$1 want_status=$2 want_text=${3:-}
  if [ "$status" -eq "$want_status" ] && { [ -z "$want_text" ] || grep -qF -- "$want_text" <<<"$out"; }; then
    echo "ok   $what"
  else
    echo "FAIL $what (status $status, wanted $want_status, text '$want_text')"
    echo "     | ${out//$'\n'/$'\n'     | }"
    fails=1
  fi
}

cmd=start
run STUB_BOOT_AFTER=2
expect "start creates the AVD and waits for boot" 0 "booted"
ok_if "AVD created from the pinned system image" grep -qF 'system-images;android-35;google_apis;x86_64' "$tmp/avdmanager"
for flag in -no-window -no-audio -gpu; do
  ok_if "emulator launched with $flag" grep -qF -- "$flag" "$tmp/emulator"
done
ok_if "AVD lives under XDG_DATA_HOME" test -d "$tmp/data/paseo-dev/android/avd/paseo-dev-android-35.avd"
ok_if "nothing written under HOME" test ! -e "$tmp/home"

run STUB_BOOT_AFTER=0
expect "second start is idempotent while running" 0 "already running"
ok_if "existing AVD is not recreated" test "$(wc -l <"$tmp/avdmanager")" -eq 1

cmd=stop
run
expect "stop ends the emulator" 0 "stopped"
run
expect "stop when not running is a no-op" 0 "not running"

cmd=start
run PASEO_DEV_KVM_DEVICE="$tmp/missing"
expect "missing virtualization device is named" 1 "kvm"

run STUB_EMULATOR_FAILS=1
expect "emulator dying early fails with its log" 1 "emulator exploded"

run
expect "boot that never completes times out" 1 "timed out"
cmd=stop
run

cmd=bogus
run
expect "unknown subcommand prints usage" 2 "usage"

exit "$fails"
