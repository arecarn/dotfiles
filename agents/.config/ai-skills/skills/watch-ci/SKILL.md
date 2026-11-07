---
description: Use after pushing a commit when the CI result is not yet known, or when asked to watch, check, or babysit CI, a pipeline, a build, or a red run — on GitHub Actions or GitLab CI.
---

# Watch CI

A green local lint run is not evidence about CI. Every push gets watched to its
conclusion, and the conclusion decides what happens next.

Three things generalize across providers, and `watch.sh` (beside this file)
implements them:

1. **The run is identified by commit SHA *and* workflow, not by branch.** Several
   runs can be in flight on one branch, and one commit usually has several runs,
   so the newest run on the right SHA is often the wrong workflow.
2. **Branch on the reported status, not on a CLI's exit code.** Both providers
   exit non-zero for "cancelled" exactly as they do for "failed", and those
   demand opposite responses.
3. **A dead watch command is not a result.** A dropped connection also exits
   non-zero and looks like a red build. The script loops until the API reports a
   terminal status. If no status ever arrives, report that the watch failed,
   never that the run failed.

## Run the watch without blocking the session

CI takes minutes, so run the script in the background and let its result arrive
later. The tool that does that differs per harness:

| Harness | Binding |
|---|---|
| Claude Code | The `Monitor` tool. Arm it on the script; it streams the final line back. |
| pi | The `monitor` tool. Arm it on the script with `maxEvents: 1`; a one-shot monitor wakes the session by default, so `wake` need not be passed, and it disarms itself once the line arrives. |
| anything else | Whatever runs a command detached and reports back later. |

If the harness has no such mechanism, say the watch will block before starting
it, rather than silently tying up the session. Never swap in a shorter foreground
poll to skip the setup.

```bash
watch.sh [--provider github|gitlab] [--sha SHA] [WORKFLOW_FILE]
```

It prints one line and exits 0 on any terminal status: the conclusion, the run
URL, and on GitHub the workflow, the SHA and every job's conclusion. Exit 2 means
it could not start: no CI config, both providers present (pass `--provider` for
the one you pushed to and say which you picked), or several GitHub workflows
(pass the file).

- **Detection is by CI config file, not remote.** `.github/workflows/` means
  GitHub Actions (`gh`); `.gitlab-ci.yml` means GitLab CI (`glab`). Jenkins,
  CircleCI, Azure and the rest have no recipe here: stop and ask. If the CLI for
  the detected provider is not installed, say so rather than scraping a web URL.
- **GitHub needs the workflow file, not its display name.** GitHub attaches its
  own runs to your commit (Dependency Graph, CodeQL, Dependabot); they are not in
  `.github/workflows/`, and a green "Graph Update" reads exactly like a green
  build. Confirm the line's `workflow=` is the one you meant.
- **GitLab can carry several pipelines per SHA** (push, merge request,
  scheduled). The script takes the newest and prints its `source=`; list the
  rest with `glab api "projects/:id/pipelines?sha=$sha" --jq '.[] | "\(.id)
  \(.source) \(.status)"'` if that source is not the one you expected.
- **On a matrix build, cite the legs the line reports.** A claim about one
  platform is only evidence if the reported jobs name that platform.

## Act on the status

| GitHub | GitLab | Meaning | Action |
|---|---|---|---|
| `success` | `success` | green | Report in one line. Done. |
| `cancelled` | `canceled` | superseded or cancelled by hand | Stop. Do not investigate. If a newer commit of yours replaced it, re-arm on the new SHA. |
| `failure` | `failed` | real breakage | Investigate, then propose a fix. |
| `timed_out`, `startup_failure` | `skipped`, `manual` | infrastructure or gating, not your diff | Report verbatim; say it is not a code failure. |

The spelling differs: GitHub reports `cancelled`, GitLab `canceled`. A check that
matches only one silently misclassifies the other.

Repos that auto-cancel superseded runs (GitHub `concurrency.cancel-in-progress`,
GitLab `interruptible`) make "cancelled" the *normal* result of pushing twice in
quick succession. Treating it as red wastes an investigation on a run that was
replaced on purpose.

## On failure

1. Pull the failing logs: `gh run view <id> --log-failed` on GitHub; on GitLab
   `glab api "projects/:id/pipelines/$id/jobs" --jq '.[] |
   select(.status=="failed") | "\(.id) \(.name)"'`, then `glab ci trace <job-id>`.
2. Read the actual failing step. On a matrix build, check whether one leg failed
   or all of them: a single-platform failure points at path, symlink, or
   line-ending handling rather than the logic.
3. Check the repo's recorded traps before debugging from scratch, if it keeps any:
   `grep -ri "<symptom>" docs/gotchas/`
4. Propose the fix with the evidence behind it. Do not push a speculative fix to
   see whether CI goes green: that costs a full pipeline per guess and pollutes
   history.

Dispatch a background subagent to investigate when the log is long or several
jobs failed. Skip it for a one-line lint error already visible in the output.

## Common mistakes

- **Running the watch as a foreground call.** It ties up the session for minutes.
- **Describing jobs you did not read.** "Both matrix legs passed" is a claim
  about the jobs list; if the run had no matrix, it is invented.
- **Reporting a cancelled run as a failure.** It means "replaced", not "broken".
- **Watching a SHA you then rewrote.** Amending or rebasing after arming the
  watch orphans it: the old run keeps going and its result is meaningless. Stop
  that watch and re-arm on the new SHA.
