---
name: watch-ci
description: Use after pushing a commit when the CI result is not yet known, or when asked to watch, check, or babysit CI, a pipeline, a build, or a red run — on GitHub Actions or GitLab CI.
---

# Watch CI

A green local lint run is not evidence about CI. Every push gets watched to its
conclusion, and the conclusion decides what happens next.

Two things generalize across providers, and everything below is a consequence of them:

1. **Identify the run by commit SHA, not by branch.** Several runs can be in flight on
   one branch, so the newest branch run is often an earlier commit's.
2. **Branch on the reported status, not on the CLI's exit code.** Both providers exit
   non-zero for "cancelled" exactly as they do for "failed", and those demand opposite
   responses.

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

## GitHub Actions

Run with the `Monitor` tool, never a blocking `Bash` call — CI takes minutes. Prints one
line: the conclusion plus the run URL.

```bash
sha=$(git rev-parse HEAD)
until id=$(gh run list --commit "$sha" --limit 1 \
    --json databaseId --jq '.[0].databaseId') && [ -n "$id" ]; do
    sleep 5
done
gh run watch "$id" --exit-status > /dev/null 2>&1
gh run view "$id" --json conclusion,url --jq '"\(.conclusion) \(.url)"'
```

Add `--workflow <name>` to both `gh run list` and `gh run view` when a repo runs several
workflows per push and only one matters.

Failure logs: `gh run view <id> --log-failed`

## GitLab CI

```bash
sha=$(git rev-parse HEAD)
until id=$(glab api "projects/:id/pipelines?sha=$sha" --jq '.[0].id') && [ -n "$id" ]; do
    sleep 5
done
until status=$(glab api "projects/:id/pipelines/$id" --jq '.status') \
    && ! echo "$status" | grep -qE '^(created|waiting_for_resource|preparing|pending|running)$'; do
    sleep 30
done
glab api "projects/:id/pipelines/$id" --jq '"\(.status) \(.web_url)"'
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

- **Blocking on the watch command in a `Bash` call.** Ties up the session for minutes. Use `Monitor`.
- **Selecting the run by branch.** Picks whichever run is newest, which may be another
  commit's or one you already superseded.
- **Reporting a cancelled run as a failure.** It means "replaced", not "broken".
- **Watching a SHA you then rewrote.** Amending or rebasing after arming the monitor
  orphans it — the old run keeps going and its result is meaningless. Stop that monitor
  and re-arm on the new SHA.
