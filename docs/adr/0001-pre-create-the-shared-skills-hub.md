# Pre-create the shared skills hub before stowing

The `agents` stow package exists in both this repo and `dotfiles_local`, so two
independent dploy runs write into `~/.config/ai-skills`. Not every machine has
both: on a personal machine the hub may show only this repo's skills, which
makes the pre-create look like it is guarding nothing. It is not — work
machines run both repos, and that is where the damage would land. `Dploy.stow` creates
that directory and its `skills` child as real directories first, which looks
like dead code — the stow would create them anyway — but constrains where dploy
is allowed to fold, and is load-bearing.

## Why

dploy folds a fully-owned directory into a single symlink and unfolds it again
when a second source needs to share it. Unfolding is only correct near the leaf.
Without the pre-create, stowing the first repo folds high, at `~/.config`, and
stowing the second repo then unfolds one level and writes its links **inside the
first repo's working tree**, at the wrong relative depth:

    repoA/agents/.config/ai-skills/skills/b-skill -> ../../../../repoB/...   (dangling)

The second repo's git tree gains a stray entry, the link is broken, and a later
unstow fails with `ConflictsWithExistingLink`, leaving the mess in place.

With the directories pre-created, folding can only ever happen at the `skills`
level, where dploy's unfold computes the right paths.

## Consequences

Unstowing one repo still re-folds `skills` into a symlink into the other repo —
the pre-create does not prevent folding, only where it happens. That state is
self-healing: the next `inv stow` pre-creates over it (`mkdir(exist_ok=True)`
tolerates a symlink to a directory) and dploy unfolds it correctly. A full
stow / unstow / re-stow cycle across both repos ends clean.

Verified experimentally against dploy 0.1.3 rather than by reading its source;
the folding behaviour is not documented and the wrong-depth unfold looks like a
dploy bug, so an upgrade should be re-tested rather than assumed compatible.

The pre-create is `skills_hub.pre_create`, and `tests/test_skills_hub.py` is the
re-test: it stows two source trees that both contribute an `agents` stow package
into a temporary home and asserts this invariant. Run it when bumping dploy.
