# A push passes every local check and still breaks CI

**The pre-push hook runs only `inv lint`, while CI also runs `provision` and
`stow` on bare Linux and Windows runners — so the steps that fail most often are
the ones never exercised before the push.**

`provision` is the usual culprit, and it is invisible locally for a structural
reason: on a machine that is already provisioned, nearly every Ansible task is a
no-op that reports `ok`. The bare runner is the only place the install paths
actually execute, so a broken one passes locally and fails there.

The consequence is a workflow rule rather than a code fix: never treat a green
local run as evidence, watch the CI run after every push. `AGENTS.md` has the
command and the reporting expectation.

Two known shapes of runner-only failure:

- [Desktop-only Ansible tasks](desktop-only-ansible-tasks-fail-on-ci.md), which
  have no session to act on.
- Rate limits and other shared-infrastructure limits keyed to the runner's IP
  rather than to this repo.

**Confirmed:** unknown, predates this convention — migrated from `AGENTS.md`.
