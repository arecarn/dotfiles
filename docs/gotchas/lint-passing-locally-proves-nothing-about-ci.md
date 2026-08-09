# A push passes every local check and still breaks CI

**No git hook runs `inv lint`, and nothing local runs `provision` or `stow` at
all — so every step CI actually fails on is one no local check ever exercised.**

The hooks cover something else entirely: `pre-commit` runs the whitespace, ASCII
filename, copyright, and shebang checks, and `pre-push` runs the fixup/WIP and
branch-name checks. Linting is a command you remember to type.

`provision` is the usual culprit, and it is invisible locally for a structural
reason: on a machine that is already provisioned, nearly every Ansible task is a
no-op that reports `ok`. The bare runner is the only place the install paths
actually execute, so a broken one passes locally and fails there. `stow` is the
same story — CI runs it against a home directory with nothing in it.

The consequence is a workflow rule rather than a code fix: never treat a green
local run as evidence, watch the CI run after every push. `AGENTS.md` has the
command and the reporting expectation.

Two known shapes of runner-only failure:

- [Desktop-only Ansible tasks](desktop-only-ansible-tasks-fail-on-ci.md), which
  have no session to act on.
- Rate limits and other shared-infrastructure limits keyed to the runner's IP
  rather than to this repo.

**Confirmed:** 2026-08-09, against `git/.config/git/hooks/` and
`.github/workflows/ci.yml` at 87e2edc. Run 31319928297 failed at
`Provision (headless)` on a commit whose only change was a workflow trigger,
while `inv lint` passed locally on the same tree.
