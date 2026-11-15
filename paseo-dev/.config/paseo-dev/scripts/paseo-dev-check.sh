# shellcheck shell=bash
# Report host prerequisites and version drift for Paseo development. Run from
# a Paseo checkout. Warn-only: always exits 0, because none of these block
# work that does not need them (virtualization is only for the Android
# emulator).
#
# Both comparisons are against the checkout in the current directory: the Node
# major it pins (.tool-versions, else package.json engines) and the Playwright
# its package-lock.json locks. Nothing is hardcoded here, so a Paseo bump
# needs no edit.
#
# Each PASEO_DEV_* variable overrides what the check reads, so the behavior
# tests can simulate a host. An empty PASEO_DEV_INSTALLED_PLAYWRIGHT means
# "not installed".
kvm=${PASEO_DEV_KVM_DEVICE:-/dev/kvm}
watch_file=${PASEO_DEV_WATCH_LIMIT_FILE:-/proc/sys/fs/inotify/max_user_watches}
min_watches=${PASEO_DEV_MIN_WATCHES:-262144}
shell_node_major=${PASEO_DEV_SHELL_NODE_MAJOR:-$(node -p 'process.versions.node.split(".")[0]' 2>/dev/null || echo unknown)}
installed_playwright=${PASEO_DEV_INSTALLED_PLAYWRIGHT-$(./node_modules/.bin/playwright --version 2>/dev/null | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)}

# The repo's Node major, or empty when the checkout pins none.
repo_node_major() {
  local pin=""
  if [ -f .tool-versions ]; then
    pin=$(awk '$1 == "nodejs" || $1 == "node" { print $2; exit }' .tool-versions)
  fi
  if [ -z "$pin" ] && [ -f package.json ]; then
    pin=$(jq -r '.engines.node // empty' package.json 2>/dev/null)
  fi
  # First integer: "22.20.0" and ">=22 <23" both give 22.
  grep -oE '[0-9]+' <<<"$pin" | head -1
}
repo_node=$(repo_node_major)

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

if [ -n "$repo_node" ] && [ "$shell_node_major" != "$repo_node" ]; then
  warn "node-drift: shell Node major is $shell_node_major, the repo pins $repo_node. Enter the dev shell or update the flake's Node version."
fi

locked=$(jq -r '.packages["node_modules/playwright"].version // empty' package-lock.json 2>/dev/null)
if [ -z "$locked" ]; then
  warn "playwright-drift: no Playwright version found in ./package-lock.json; run from a Paseo checkout."
elif [ -n "$installed_playwright" ] && [ "$locked" != "$installed_playwright" ]; then
  warn "playwright-drift: lock file has Playwright $locked, installed is $installed_playwright. Re-run paseo-install."
fi

[ "$warnings" -eq 0 ] && echo "all prerequisites ok"
exit 0
