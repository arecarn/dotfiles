# `uv.lock` shows hundreds of changed URLs nobody edited

**Any `uv run` on a machine configured against an internal package index rewrites
every URL in `uv.lock` to that index, so a diff of ~250 changed lines appears
after running an unrelated task.**

The rewrite is silent and total: `source = { registry = ... }`, every `sdist`
url, every `wheels` url, plus `revision = 3` added at the top. `uv sync` does not
do it. Only `uv run` does, which is how every task in this repo is invoked
(`uv run inv lint`, `uv run pytest`), so it happens constantly and has nothing to
do with the change being worked on.

Two reasons it matters here rather than being cosmetic:

- This repo is public. The rewritten URLs name an internal host, and this repo's
  own conventions bar internal registries from it.
- The diff is large enough to bury a real lockfile change, and small enough in
  intent (a mirror, same hashes) to look harmless in review.

Revert before every commit, and never `git add -A` in this repo:

```sh
git checkout -- uv.lock
```

The index comes from the machine's uv configuration (`UV_INDEX_URL` /
`UV_DEFAULT_INDEX` or a `uv.toml`), not from anything in the checkout, so a
clean clone on the same machine reproduces it immediately.

**Confirmed:** 2026-08-25, twice in one day. Hit while committing the Windows CI
provisioning fix, and again independently while adding the herdr provisioning
task -- the second time without knowledge of the first, which is what moved this
from a note in a handoff to an entry here. Both times the whole lockfile was
rewritten to `artifactory.blueorigin.com` by an ordinary `uv run inv lint`.
