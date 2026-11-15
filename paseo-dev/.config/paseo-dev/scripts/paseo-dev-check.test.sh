# shellcheck shell=bash
# Behavior tests for paseo-dev-check. Each case simulates one host condition
# through the check's environment overrides and asserts the named message and
# the exit status. Run: bash paseo-dev-check.test.sh [path-to-check]
set -u
here=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
check=${1:-$here/paseo-dev-check.sh}
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT

# A healthy baseline; each case breaks exactly one thing.
touch "$tmp/kvm"
echo 524288 >"$tmp/watches"
mkdir "$tmp/repo"
lock() {
  echo "{\"packages\":{\"node_modules/playwright\":{\"version\":\"$1\"}}}" >"$tmp/repo/package-lock.json"
}
lock 1.58.2

run() {
  out=$(cd "$tmp/repo" && env \
    PASEO_DEV_KVM_DEVICE="$tmp/kvm" \
    PASEO_DEV_WATCH_LIMIT_FILE="$tmp/watches" \
    PASEO_DEV_NODE_MAJOR=22 \
    PASEO_DEV_PLAYWRIGHT_VERSION=1.58.2 \
    "$@" bash "$check" 2>&1)
  status=$?
}

fails=0
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

run
expect "healthy host: exit 0" 0 "all prerequisites ok"

run PASEO_DEV_KVM_DEVICE="$tmp/missing"
expect "missing virtualization device is named, exit 0" 0 "WARN kvm:"
expect "missing virtualization says what to do" 0 "usermod -aG kvm"

chmod 000 "$tmp/kvm"
if [ -r "$tmp/kvm" ]; then
  echo "skip kvm unreadable (user ignores file modes)"
else
  run
  expect "unreadable virtualization device is named, exit 0" 0 "WARN kvm:"
fi
chmod 644 "$tmp/kvm"

echo 8192 >"$tmp/watches"
run
expect "low file-watcher limit is named, exit 0" 0 "WARN watch-limit:"
expect "low watcher limit says how to raise it" 0 "fs.inotify.max_user_watches"
echo 524288 >"$tmp/watches"

run PASEO_DEV_NODE_MAJOR=20
expect "node major drift warns, exit 0" 0 "WARN node-drift:"

lock 1.50.0
run
expect "playwright drift warns, exit 0" 0 "WARN playwright-drift:"

rm "$tmp/repo/package-lock.json"
run
expect "no lock file is a warning, exit 0" 0 "WARN playwright-drift:"

exit "$fails"
