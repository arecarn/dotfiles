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
check "xvfb-run resolves" command -v xvfb-run
check "Xvfb resolves" command -v Xvfb
check "paseo-desktop-capture resolves" command -v paseo-desktop-capture

exit "$fail"
