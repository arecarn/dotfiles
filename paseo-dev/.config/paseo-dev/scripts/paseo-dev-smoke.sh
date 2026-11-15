# shellcheck shell=bash
# Assert the toolchain inside the dev shell. Exits non-zero on any failure.
fail=0
check() {
  local what=$1
  shift
  if "$@" >/dev/null 2>&1; then
    echo "ok   $what"
  else
    echo "FAIL $what"
    fail=1
  fi
}

node_major=$(node -p 'process.versions.node.split(".")[0]')
check "node major is 22 (got $node_major)" test "$node_major" = 22
check "python3 resolves" python3 --version
check "gcc resolves" gcc --version
check "g++ resolves" g++ --version
check "make resolves" make --version

# The Android variant (`nix develop .#android`) is checked only when asked for:
# `paseo-dev-smoke android`. The default shell must not carry any of it.
if [ "${1:-}" = android ]; then
  check "ANDROID_HOME is set" test -n "${ANDROID_HOME:-}"
  check "JAVA_HOME is set" test -n "${JAVA_HOME:-}"
  java_major=$(java -version 2>&1 | sed -n '1s/.*version "\([0-9]*\).*/\1/p')
  check "java major is 21 (got $java_major)" test "$java_major" = 21
  check "gradle resolves" gradle --version
  check "adb resolves" adb --version
  check "emulator resolves" emulator -version
  check "sdkmanager resolves" command -v sdkmanager
  # ANDROID_PLATFORM / ANDROID_BUILD_TOOLS come from the flake's one definition.
  sdk=${ANDROID_HOME:-/nonexistent}
  check "platform-tools in SDK" test -x "$sdk/platform-tools/adb"
  check "emulator in SDK" test -x "$sdk/emulator/emulator"
  check "platform ${ANDROID_PLATFORM:-?} in SDK" test -d "$sdk/platforms/android-${ANDROID_PLATFORM:-?}"
  check "build-tools ${ANDROID_BUILD_TOOLS:-?} in SDK" test -d "$sdk/build-tools/${ANDROID_BUILD_TOOLS:-?}"
  check "x86_64 google_apis image in SDK" test -d "$sdk/system-images/android-${ANDROID_PLATFORM:-?}/google_apis/x86_64"
else
  check "default shell has no ANDROID_HOME" test -z "${ANDROID_HOME:-}"
fi

exit "$fail"
