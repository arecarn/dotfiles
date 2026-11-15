# shellcheck shell=bash
# Report host prerequisites and version drift for Paseo development. Run from
# a Paseo checkout. Warn-only: always exits 0, because none of these block
# work that does not need them (virtualization is only for the Android
# emulator).
#
# Each PASEO_DEV_* variable overrides what the check reads, so the behavior
# tests can simulate a host. The expected versions below are the ones to bump
# when the Paseo repo moves (CI uses Node 22 via setup-node).
kvm=${PASEO_DEV_KVM_DEVICE:-/dev/kvm}
watch_file=${PASEO_DEV_WATCH_LIMIT_FILE:-/proc/sys/fs/inotify/max_user_watches}
min_watches=${PASEO_DEV_MIN_WATCHES:-262144}
ci_node_major=${PASEO_DEV_CI_NODE_MAJOR:-22}
expected_playwright=${PASEO_DEV_PLAYWRIGHT_VERSION:-1.58.2}
node_major=${PASEO_DEV_NODE_MAJOR:-$(node -p 'process.versions.node.split(".")[0]' 2>/dev/null || echo unknown)}

warnings=0
warn() {
  echo "WARN $1"
  warnings=$((warnings + 1))
}

if [ ! -r "$kvm" ] || [ ! -w "$kvm" ]; then
  warn "kvm: $kvm is missing or not usable by this user; the Android emulator cannot run. Join the group that owns it: sudo usermod -aG kvm \"\$USER\", then log in again."
fi

watches=$(cat "$watch_file" 2>/dev/null || echo 0)
if [ "$watches" -lt "$min_watches" ]; then
  warn "watch-limit: inotify watch limit is $watches, below $min_watches; Metro fails with ENOSPC. Raise it: sudo sysctl fs.inotify.max_user_watches=524288 (persist in /etc/sysctl.d/)."
fi

if [ "$node_major" != "$ci_node_major" ]; then
  warn "node-drift: shell Node major is $node_major, CI uses $ci_node_major. Enter the dev shell or update the flake."
fi

locked=$(jq -r '.packages["node_modules/playwright"].version // empty' package-lock.json 2>/dev/null)
if [ -z "$locked" ]; then
  warn "playwright-drift: no Playwright version found in ./package-lock.json; run from a Paseo checkout after install."
elif [ "$locked" != "$expected_playwright" ]; then
  warn "playwright-drift: lock file has Playwright $locked, this check expects $expected_playwright. Update the expectation in paseo-dev-check.sh if the bump is intended."
fi

[ "$warnings" -eq 0 ] && echo "all prerequisites ok"
exit 0
