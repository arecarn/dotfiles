# Windows CI fails with `'<tool>' is not recognized` after a successful choco install

**The Windows CI job intermittently fails with `'<tool>' is not recognized as an
internal or external command` for a tool `choco install` reported installing
successfully in an earlier step — and re-running the failed job on the same
commit passes.** First seen with `shellcheck`; the same mechanism covers every
choco-installed linter the Windows job uses, now `stylua` and `selene`.

The symptom reads like a real failure of whatever step used the tool: it prints
the full command line it was about to run, then exits 1. Nothing in the output
says the binary is missing rather than the input being wrong, so the first
instinct is to go looking at the diff.

What rules out the diff: re-running the *same job* on the *same commit*
succeeds. It is not the commit, not the file list, and not a tool version
difference — the only thing that changed between the two runs is the runner.

`choco install` exits 0 and the step is marked successful, so the install is not
reporting the problem. Whatever the mechanism — a shim not yet written, a PATH
entry not visible to the next step's process — it is not observable from the
step that fails.

Getting past it: re-run the failed job (`gh run rerun <id> --failed`) before
investigating anything. If it passes, this was it.

A missing linter is a hard error under CI by policy — see the missing-linter
comment above `_run_linter` in `tasks.py` — so this trap now surfaces as an
explicit "not found on PATH" lint failure rather than a silently skipped check.
That is deliberate: a green lint that checked nothing is the worse outcome.

**Confirmed:** 2026-08-20 against
[run 32432887500](https://github.com/arecarn/dotfiles/actions/runs/32432887500)
on `windows-latest`, then with `shellcheck` installed by `choco install`.
Shellcheck no longer runs on Windows as of arecarn/dotfiles#27; the entry is
kept because `stylua` and `selene` still reach that runner the same way.
