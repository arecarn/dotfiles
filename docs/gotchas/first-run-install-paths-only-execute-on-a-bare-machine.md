# A new provisioning task passes locally three times and fails CI three times

**Every prerequisite a new install task needs already exists on the machine you
wrote it on, so its first-run path is the one path you cannot test there — and
each failure only reveals the next missing prerequisite, one CI round at a time.**

This is the sharp edge of [lint passing locally proving nothing about
CI](lint-passing-locally-proves-nothing-about-ci.md). That entry explains why an
already-provisioned machine reports `ok` for tasks that would fail on a bare one.
This one is about the specific cost: the failures arrive in sequence, because
fixing the first prerequisite lets the play reach the second.

Adding one `ansible/tasks/herdr.yml` took three runs, each a real bug, none
reproducible locally:

| Round | Failure | Why the dev machine hid it |
|---|---|---|
| 1 | Play killed with no ansible error at all | `uri: return_content: true` registered a 155 KB manifest (release notes for 55 versions). Enough RAM locally; the runner killed it. |
| 2 | `object of type 'dict' has no attribute 'stdout_lines'` | A status task gated on `stat.exists` skipped, so its result was never registered. The binary already existed locally, so the gate was always true. |
| 3 | `pi extension directory not found ... install pi first` | `herdr integration install` needs `~/.pi/agent/extensions`, created by stow's fold barriers. Locally it had existed for months. |

Round 1 is worth recognising on sight: **a play that ends mid-task with no
`fatal:` line was killed, not failed.** Look for a large registered variable
before anything else. `retries` never fires either, which is the tell that nothing
in ansible ran.

What actually shortens the loop is simulating the bare machine locally, which is
cheap and was available the whole time:

```sh
# A HOME with none of the prerequisites, to exercise the first-run path.
rm -rf /tmp/fakehome && mkdir -p /tmp/fakehome/.local/bin
HOME=/tmp/fakehome uv run ansible-playbook -i localhost, /tmp/sim.yml -c local
```

Watch for the trap inside the trap: a tool that resolves paths from `$HOME` at
runtime may still read the real one, so `herdr integration status` reported
`pi: current` against `~/.pi` while pointed at a fake home. Check what the command
prints, not just that it exited 0.

Ordering is the other thing to state rather than assume. `provision` runs before
`stow`, and `setup_ai` is a `post` hook of `provision` — so it is also before
`stow`, despite reading like a final step. Anything needing a stowed path belongs
in `stow`.

**Confirmed:** 2026-08-26. Runs 32996363956, 33001373808 and 33002556656 failed in
that order on `rcarney/herdr-provisioning`, each at `Provision (headless)`, while
`inv lint`, `pytest` and `--tags herdr --check` passed locally on every one of the
same trees. Run 33004041090 was green once all three prerequisites were handled.
