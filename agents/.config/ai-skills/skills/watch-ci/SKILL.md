---
name: watch-ci
description: Use after pushing a commit when the CI result is not yet known, or when asked to watch, check, or babysit CI, a pipeline, a build, or a red run — on GitHub Actions or GitLab CI.
---

# Watch CI

A green local lint run is not evidence about CI. Every push gets watched to its
conclusion, and the conclusion decides what happens next.

Two things generalize across providers, and everything below is a consequence of them:

1. **Identify the run by commit SHA *and* workflow, not by branch.** Several runs can be
   in flight on one branch, so the newest branch run is often an earlier commit's — and
   one commit usually has several runs, so the newest run on the right SHA is often the
   wrong workflow.
2. **Branch on the reported status, not on the CLI's exit code.** Both providers exit
   non-zero for "cancelled" exactly as they do for "failed", and those demand opposite
   responses.
3. **A dead watch command is not a result.** A dropped connection
   (`error connecting to api.github.com`) also exits non-zero, and looks identical to a
   red build. Both recipes below loop until the API reports a terminal status, so a blip
   costs a retry instead of a false alarm. If no status ever arrives, report that the
   watch failed — never that the run failed.

## Detect the provider first

**The CI config file in the repo is the signal, not the remote host.** A repo's config
file names the system that actually runs the pipeline; a remote URL only suggests it.
Self-hosted GitLab commonly lives on a hostname with no "gitlab" in it, and a GitHub
mirror of a GitLab-run repo points at the wrong provider entirely.

```bash
ls -d .github/workflows .gitlab-ci.yml Jenkinsfile .circleci azure-pipelines.yml \
    .travis.yml bitbucket-pipelines.yml 2>/dev/null
git remote -v
```

| Config file present | Provider | CLI |
|---|---|---|
| `.github/workflows/` | GitHub Actions | `gh` |
| `.gitlab-ci.yml` | GitLab CI | `glab` |
| `Jenkinsfile`, `.circleci/`, `azure-pipelines.yml`, others | no CLI recipe here | Stop and ask |
| none | no CI in this repo | Say so; there is nothing to watch |

Read the remote only after the file check, and only to pick the host the CLI talks to
(`glab` needs `GITLAB_HOST` or a configured remote for self-hosted instances).

**When both `.github/workflows/` and `.gitlab-ci.yml` exist**, the repo is mirrored or
mid-migration — watch the one whose remote you actually pushed to, and say which you
picked rather than silently choosing.

If the CLI for the detected provider is not installed, say so and ask how to proceed
rather than falling back to scraping a web URL.

## Run the watch without blocking the session

CI takes minutes, so the loops below must not run in a foreground call that holds the
session until they finish. What matters is the capability: run the loop in the background
and deliver its result later. The tool that provides it differs per harness, so bind the
capability to whatever the running harness actually has.

| Harness | Binding |
|---|---|
| Claude Code | The `Monitor` tool. Arm it on the loop; it streams the final line back. |
| pi | The `monitor` tool. Arm it on the loop with `maxEvents: 1`; a one-shot monitor wakes the session by default, so `wake` need not be passed, and it disarms itself once the line arrives. |
| anything else | Whatever runs a command detached and reports back later. |

If the harness has no such mechanism, say the watch will block before starting it, rather
than silently tying up the session. Never swap in a shorter foreground poll to skip the
setup: that is the failure this section exists to prevent.

## GitHub Actions

Run it in the background per the binding above. Prints one line: the conclusion plus the
run URL.

Set `wf` to the workflow file you care about — `ls .github/workflows/` names the
candidates. Pass the **file**, not the display `name:` inside it: the file is what fails
loudly on a typo (`HTTP 404: workflow nope.yml not found`), where a wrong display name
silently matches nothing and the loop waits forever.

```bash
sha=$(git rev-parse HEAD)
wf=ci.yml
# `// empty` matters: without it, no run yet yields the string "null", which passes
# the -n test and watches a run id that does not exist.
until id=$(gh run list --commit "$sha" --workflow "$wf" --limit 1 \
    --json databaseId --jq '.[0].databaseId // empty') && [ -n "$id" ]; do
    sleep 5
done
# Re-enter the watch if it drops; a lost connection is not a finished run.
until conclusion=$(gh run view "$id" --json conclusion --jq '.conclusion') \
    && [ -n "$conclusion" ]; do
    gh run watch "$id" > /dev/null 2>&1 || sleep 30
done
gh run view "$id" --json conclusion,url --jq '"\(.conclusion) \(.url)"'
```

**`--workflow` is not optional.** GitHub attaches its own runs to your commit —
Dependency Graph, CodeQL, Dependabot — and they are not in `.github/workflows/`, so
nothing in the repo hints they exist. Without the flag, `--limit 1` returns whichever run
finished last, and a green "Graph Update" reads exactly like a green build. Confirm the
run you watched is the one you meant:

```bash
gh run view "$id" --json workflowName,headSha --jq '"\(.workflowName) \(.headSha)"'
```

On a matrix build, cite the legs rather than asserting them — a claim about one platform
is only evidence if you read that leg:

```bash
gh run view "$id" --json jobs --jq '.jobs[] | "\(.name): \(.conclusion)"'
```

Failure logs: `gh run view <id> --log-failed`

## GitLab CI

```bash
sha=$(git rev-parse HEAD)
# `// empty` for the same reason as the GitHub recipe: no pipeline yet prints "null".
until id=$(glab api "projects/:id/pipelines?sha=$sha" --jq '.[0].id // empty') && [ -n "$id" ]; do
    sleep 5
done
until status=$(glab api "projects/:id/pipelines/$id" --jq '.status') \
    && ! echo "$status" | grep -qE '^(created|waiting_for_resource|preparing|pending|running)$'; do
    sleep 30
done
glab api "projects/:id/pipelines/$id" --jq '"\(.status) \(.web_url)"'
```

One SHA can carry several pipelines here too — a push pipeline plus a merge-request one,
or a scheduled or triggered run — so `.[0]` is "newest", not "mine". Print what you
selected before trusting it, and filter by `source` when the SHA carries more than one:

```bash
glab api "projects/:id/pipelines?sha=$sha" --jq '.[] | "\(.id) \(.source) \(.status)"'
```

`glab ci status` watches the current branch's latest pipeline, which is the branch-based
selection this skill exists to avoid — use it only for a quick interactive glance, never
as the monitor.

Failure logs: `glab ci trace <job-id>`, after `glab api "projects/:id/pipelines/$id/jobs"
--jq '.[] | select(.status=="failed") | "\(.id) \(.name)"'`

## Act on the status

| GitHub | GitLab | Meaning | Action |
|---|---|---|---|
| `success` | `success` | green | Report in one line. Done. |
| `cancelled` | `canceled` | superseded or cancelled by hand | Stop. Do not investigate. If a newer commit of yours replaced it, re-arm on the new SHA. |
| `failure` | `failed` | real breakage | Investigate, then propose a fix. |
| `timed_out`, `startup_failure` | `skipped`, `manual` | infrastructure or gating, not your diff | Report verbatim; say it is not a code failure. |

Note the spelling differs: GitHub reports `cancelled`, GitLab `canceled`. A status check
that matches only one silently misclassifies the other.

Repos that auto-cancel superseded runs (GitHub `concurrency.cancel-in-progress`, GitLab
`interruptible`) make "cancelled" the *normal* result of pushing twice in quick
succession. Treating it as a red build wastes an investigation on a run that was replaced
on purpose.

## On failure

1. Pull the failing logs with the provider command above.
2. Read the actual failing step. On a matrix build, check whether one leg failed or all of
   them — a single-platform failure points at path, symlink, or line-ending handling
   rather than at the logic.
3. Check the repo's recorded traps before debugging from scratch, if it keeps any:
   `grep -ri "<symptom>" docs/gotchas/`
4. Propose the fix with the evidence behind it. Do not push a speculative fix to see
   whether CI goes green — that costs a full pipeline per guess and pollutes history.

Dispatch a background subagent to investigate when the log is long or several jobs failed.
Skip it for a one-line lint error already visible in the output.

## Common mistakes

- **Running the watch as a foreground call.** Ties up the session for minutes. Use the
  background binding for the harness.
- **Selecting the run by branch.** Picks whichever run is newest, which may be another
  commit's or one you already superseded.
- **Selecting by SHA alone, without `--workflow`.** The right commit's newest run is
  routinely a GitHub-injected workflow (Dependency Graph, CodeQL) that passes in seconds
  while the real build is still going. Reporting its `success` reports nothing about the
  diff.
- **Describing jobs you did not read.** "Both matrix legs passed" is a claim about the
  jobs list; if the run had no matrix, it is invented. Print the legs.
- **Reporting a cancelled run as a failure.** It means "replaced", not "broken".
- **Watching a SHA you then rewrote.** Amending or rebasing after arming the watch
  orphans it — the old run keeps going and its result is meaningless. Stop that watch
  and re-arm on the new SHA.
