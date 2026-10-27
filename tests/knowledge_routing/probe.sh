#!/usr/bin/env bash
# Run one knowledge-routing probe as a fresh Paseo agent.
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
# Needs a running Paseo daemon and `jq`, and spends real tokens, so it is run by
# hand rather than by pytest. See README.md.
#
# Usage: probe.sh <slug> <cwd> <task-prompt>
# Writes the agent's reply to $OUT_DIR/<slug>.txt. Exit 0 with the reply on
# stdout, 2 when the agent could not be started, 3 when it answered nothing.
set -euo pipefail

slug=$1
cwd=${2/#\~/$HOME}
task=$3
OUT_DIR=${OUT_DIR:-$(dirname "$0")/results}
mkdir -p "$OUT_DIR"

# Appended rather than woven into the task, so the task itself stays a naturally
# worded request.
prompt="$task

Then, separately: list every reference document you consulted before answering,
by bundle id and path, or say NONE if you consulted none. Do not edit files."

# --new-workspace local is what makes --cwd take effect: without it the agent
# runs in the caller's own workspace and the probe would be cold about the wrong
# repository. Paseo waits for the agent to finish by default.
run_json=$(paseo run "$prompt" --provider claude --new-workspace local \
	--cwd "$cwd" --title "kb-$slug" --wait-timeout 5m --json 2>"$OUT_DIR/$slug.err") || {
	echo "could not start the probe agent for $slug:" >&2
	cat "$OUT_DIR/$slug.err" >&2
	exit 2
}

# The JSON is the last object on stdout: paseo prints a "Created workspace"
# line first when the directory had no workspace yet.
json=$(sed -n '/^{/,$p' <<<"$run_json")
agent=$(jq -r .agentId <<<"$json")
status=$(jq -r .status <<<"$json")

# Only the assistant's text, not the tool calls: the question is what the agent
# says it consulted, and a tool call's output can quote the very paths asked for.
paseo logs "$agent" --filter text >"$OUT_DIR/$slug.txt" 2>&1 || true
paseo delete "$agent" >/dev/null 2>&1 || true

# An agent that finishes without answering is indistinguishable from one that
# consulted no document -- both look like a routing miss until someone opens the
# raw file. Say so instead, because the probe is inconclusive rather than failed:
# a usage limit reached mid-run is one cause, a timeout another.
if [ "$status" != completed ] || ! grep -qi "consulted\|NONE" "$OUT_DIR/$slug.txt"; then
	echo "INCONCLUSIVE: $slug ended '$status' with no answer; its last lines were:" >&2
	grep -viE '^\s*$' "$OUT_DIR/$slug.txt" | tail -5 >&2
	exit 3
fi

cat "$OUT_DIR/$slug.txt"
