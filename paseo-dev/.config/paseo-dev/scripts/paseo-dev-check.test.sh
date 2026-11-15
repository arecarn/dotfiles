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
# The repo's Node pin, as the checkout's .tool-versions carries it.
pin_node() { printf 'rust 1.85.1\nnodejs %s\n' "$1" >"$tmp/repo/.tool-versions"; }
pin_node 22.20.0

run() {
  out=$(cd "$tmp/repo" && env \
    PASEO_DEV_KVM_DEVICE="$tmp/kvm" \
    PASEO_DEV_WATCH_LIMIT_FILE="$tmp/watches" \
    PASEO_DEV_SHELL_NODE_MAJOR=22 \
    PASEO_DEV_INSTALLED_PLAYWRIGHT=1.58.2 \
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

run PASEO_DEV_SHELL_NODE_MAJOR=20
expect "shell Node major differing from the repo pin warns, exit 0" 0 "WARN node-drift:"
expect "node drift names both majors" 0 "shell Node major is 20, the repo pins 22"

pin_node 24.1.0
run
expect "the repo pin is read, not a fixed expectation" 0 "the repo pins 24"
pin_node 22.20.0

rm "$tmp/repo/.tool-versions"
echo '{"engines":{"node":">=22 <23"}}' >"$tmp/repo/package.json"
run PASEO_DEV_SHELL_NODE_MAJOR=20
expect "engines is the fallback pin" 0 "the repo pins 22"
rm "$tmp/repo/package.json"
run
expect "no Node pin in the repo is a quiet skip, exit 0" 0 "all prerequisites ok"
pin_node 22.20.0

lock 1.50.0
run
expect "installed Playwright differing from the lock warns, exit 0" 0 "WARN playwright-drift:"
expect "playwright drift names both versions" 0 "lock file has Playwright 1.50.0, installed is 1.58.2"

lock 1.58.2
run PASEO_DEV_INSTALLED_PLAYWRIGHT=
expect "no installed Playwright is a quiet skip, exit 0" 0 "all prerequisites ok"

rm "$tmp/repo/package-lock.json"
run
expect "no lock file is a warning, exit 0" 0 "WARN playwright-drift:"

exit "$fails"
