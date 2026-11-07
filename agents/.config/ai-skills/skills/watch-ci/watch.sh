#!/usr/bin/env bash
# Watch CI for one commit until it reaches a terminal status, then print one line.
#
# Usage: watch.sh [--provider github|gitlab] [--sha SHA] [WORKFLOW_FILE]
#
# Prints "<status> <url> ..." on stdout and exits 0 once the provider reports a
# terminal status, whatever that status is: a failed or cancelled run is a
# result, not an error. Exit 2 means the script could not start (no CI config,
# ambiguous provider or workflow). A dropped connection is retried, never
# reported as a failed run.
#
# The run is selected by full commit SHA, never by branch. SHA defaults to HEAD;
# --sha accepts an abbreviation and resolves it, because both providers match
# only the full 40 characters and a short SHA would wait forever.
#
# GitHub needs WORKFLOW_FILE (the file under .github/workflows/, not its display
# name: a wrong file fails loudly, a wrong display name silently matches
# nothing) unless the repo has exactly one. The filter is not optional: GitHub
# attaches its own runs to a commit (Dependency Graph, CodeQL, Dependabot) that
# are absent from .github/workflows/ and finish in seconds.
#
# Run it detached (the harness's monitor tool); it blocks until CI finishes.

set -u

provider=""
sha=""
workflow=""
while [ $# -gt 0 ]; do
    case $1 in
        --provider) provider=${2:?--provider needs github or gitlab}; shift 2 ;;
        --sha) sha=${2:?--sha needs a commit}; shift 2 ;;
        -*) echo "watch.sh: unknown option $1" >&2; exit 2 ;;
        *) workflow=$1; shift ;;
    esac
done

sha=$(git rev-parse "${sha:-HEAD}") || exit 2

# The CI config file names the system that runs the pipeline; the remote URL
# only suggests it (self-hosted GitLab has no "gitlab" in its hostname, and a
# GitHub mirror of a GitLab-run repo points at the wrong provider).
if [ -z "$provider" ]; then
    if [ -d .github/workflows ] && [ -f .gitlab-ci.yml ]; then
        echo "watch.sh: both .github/workflows and .gitlab-ci.yml exist;" \
            "pass --provider for the one you pushed to" >&2
        exit 2
    elif [ -d .github/workflows ]; then
        provider=github
    elif [ -f .gitlab-ci.yml ]; then
        provider=gitlab
    else
        echo "watch.sh: no .github/workflows or .gitlab-ci.yml; nothing to watch" >&2
        exit 2
    fi
fi

watch_github() {
    local id conclusion file
    local -a workflows=()
    if [ -z "$workflow" ]; then
        for file in .github/workflows/*.yml .github/workflows/*.yaml; do
            [ -f "$file" ] && workflows+=("${file##*/}")
        done
        if [ "${#workflows[@]}" -ne 1 ]; then
            echo "watch.sh: pass one workflow file:" >&2
            printf '  %s\n' "${workflows[@]}" >&2
            exit 2
        fi
        workflow=${workflows[0]}
    fi
    # `// empty`: with no run yet, jq would print the string "null", which passes
    # the -n test and watches a run id that does not exist.
    until id=$(gh run list --commit "$sha" --workflow "$workflow" --limit 1 \
        --json databaseId --jq '.[0].databaseId // empty') && [ -n "$id" ]; do
        sleep 5
    done
    # Re-enter the watch if it drops; a lost connection is not a finished run.
    until conclusion=$(gh run view "$id" --json conclusion --jq '.conclusion') \
        && [ -n "$conclusion" ]; do
        gh run watch "$id" > /dev/null 2>&1 || sleep 30
    done
    # The job conclusions are in the line so a matrix claim can cite its legs.
    gh run view "$id" --json conclusion,url,workflowName,headSha,jobs --jq \
        '"\(.conclusion) \(.url) workflow=\(.workflowName) sha=\(.headSha) jobs=" + ([.jobs[] | "\(.name):\(.conclusion)"] | join(","))'
}

watch_gitlab() {
    local id pipeline_status
    # `// empty` for the same reason as the GitHub loop. One SHA can carry
    # several pipelines (push, merge request, scheduled); this takes the newest.
    until id=$(glab api "projects/:id/pipelines?sha=$sha" --jq '.[0].id // empty') \
        && [ -n "$id" ]; do
        sleep 5
    done
    # Anything not yet terminal keeps the loop going, including `canceling`,
    # which is cancellation in progress and not yet `canceled`.
    until pipeline_status=$(glab api "projects/:id/pipelines/$id" --jq '.status') \
        && ! printf '%s' "$pipeline_status" | grep -qE \
            '^(created|waiting_for_resource|preparing|waiting_for_callback|pending|running|scheduled|canceling)$'; do
        sleep 30
    done
    glab api "projects/:id/pipelines/$id" --jq '"\(.status) \(.web_url) sha=\(.sha) source=\(.source)"'
}

case $provider in
    github) watch_github ;;
    gitlab) watch_gitlab ;;
    *) echo "watch.sh: unknown provider $provider" >&2; exit 2 ;;
esac
