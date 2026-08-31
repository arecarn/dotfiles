#!/usr/bin/env bash
# Run one knowledge-routing probe in a fresh Herdr tab.
#
# A probe is a COLD agent given a realistic task that never mentions the
# knowledge system. What it measures is which entry the agent opens unprompted,
# which is the thing `agent-knowledge check` structurally cannot see: an index
# entry can match its document perfectly and still not match the tasks people
# bring.
#
# The task wording must not leak the answer -- no filename fragments, no
# "bundle", no "knowledge". A probe that names the document tests keyword
# matching, not routing.
#
# Requires a Herdr session (HERDR_ENV=1) and spends real tokens, so it is run by
# hand rather than by pytest. See README.md.
#
# Usage: probe.sh <slug> <cwd> <task-prompt>
# Writes the reply to $OUT_DIR/<slug>.txt and the tab id to <slug>.tab.
set -euo pipefail

slug=$1
cwd=$2
task=$3
OUT_DIR=${OUT_DIR:-$(dirname "$0")/results}
mkdir -p "$OUT_DIR"

if [ "${HERDR_ENV:-}" != 1 ]; then
	echo "not running inside Herdr; probe.sh needs a Herdr session" >&2
	exit 2
fi

# Appended rather than woven into the task, so the task itself stays a naturally
# worded request.
prompt="$task

Then, separately: list every reference document you consulted before answering,
by bundle id and path, or say NONE if you consulted none. Do not edit files."

tab_json=$(herdr tab create --workspace "$HERDR_WORKSPACE_ID" --cwd "$cwd" \
	--label "kb-$slug" --no-focus)
tab=$(jq -r .result.tab.tab_id <<<"$tab_json")
pane=$(jq -r .result.root_pane.pane_id <<<"$tab_json")
echo "$tab" >"$OUT_DIR/$slug.tab"

# A blocked start is usually the folder-trust dialog, and the agent stays
# readable -- report it rather than treating it as a hard failure.
if ! herdr agent start "kb-$slug" --kind claude --pane "$pane" --timeout 90000 \
	>/dev/null 2>&1; then
	echo "BLOCKED at startup: $slug" | tee "$OUT_DIR/$slug.txt"
	herdr agent read "kb-$slug" --source detection --lines 30 \
		>>"$OUT_DIR/$slug.txt" 2>&1 || true
	exit 0
fi

herdr agent prompt "kb-$slug" "$prompt" --wait --timeout 240000 >/dev/null
herdr agent read "kb-$slug" --source recent-unwrapped --lines 200 \
	>"$OUT_DIR/$slug.txt" 2>&1
cat "$OUT_DIR/$slug.txt"
