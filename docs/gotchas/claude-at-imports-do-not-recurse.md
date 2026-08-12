# A reference file that only lists `@` imports loads as nothing

**Claude Code does not expand `@` imports inside an imported file, so a hub or
index reference file whose body is just a list of `@references/...` lines
contributes only its own prose and silently drops everything it points at.**

Imports are expanded one level deep, from `CLAUDE.md` only. The obvious tidy
structure — one aggregator file importing several topic files, so the top-level
`CLAUDE.md` stays short — therefore loads none of the topics. Nothing errors;
the aggregator's own text appears, which makes it look like the import chain
worked.

Keep imported reference files self-contained. Where several topics need to arrive
through a single import (e.g. one entry point whose contents the importing repo
must not name), inline the sections into that one file rather than importing them
into it. `dotfiles_local`'s `references/local.md` is inline for exactly this
reason and says so at the top.

Verify with a fresh subprocess rather than a running session, and ask for a fact
that only the innermost file contains:

```bash
cd /tmp && claude -p 'From your instructions only: <question only the leaf file answers>' --max-turns 1
```

**Confirmed:** 2026-08-11 against Claude Code on Linux, with a two-level fixture
(`CLAUDE.md` → `references/hub.md` → `references/leaf.md`): the hub's own marker
loaded, the leaf's marker did not.
