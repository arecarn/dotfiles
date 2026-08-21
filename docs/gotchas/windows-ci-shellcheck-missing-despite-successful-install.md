# Windows CI lint fails with `'shellcheck' is not recognized`

**The Windows CI job's lint step intermittently fails with `'shellcheck' is not
recognized as an internal or external command`, even though the
`Install shellcheck (Windows)` step in the same job reported success — and
re-running the failed job on the same commit passes.**

The symptom reads like a real lint failure: the step prints the full
`shellcheck --format gcc <files>` command line it was about to run, then exits 1.
Nothing in the output says the binary is missing rather than the shell scripts
being wrong, so the first instinct is to go looking at the diff.

What rules out the diff: re-running the *same job* on the *same commit*
succeeds. It is not the commit, not the file list, and not a shellcheck version
difference — the only thing that changed between the two runs is the runner.

`choco install shellcheck` exits 0 and the step is marked successful, so the
install is not reporting the problem. Whatever the mechanism — a shim not yet
written, a PATH entry not visible to the next step's process — it is not
observable from the step that fails.

Getting past it: re-run the failed job (`gh run rerun <id> --failed`) before
investigating anything. If it passes, this was it.

Worth knowing while you are here: `lint_shell` runs `shellcheck`
unconditionally, while `lint_lua` guards each of its tools with
`shutil.which()` and skips when absent. So a missing shellcheck is a hard build
failure while a missing stylua is a silent skip. Whether the Windows job should
run shellcheck at all — the Linux job lints the same files — is tracked in
arecarn/dotfiles#27.

**Confirmed:** 2026-08-20 against
[run 32432887500](https://github.com/arecarn/dotfiles/actions/runs/32432887500)
on `windows-latest`, installing shellcheck with `choco install shellcheck`.
