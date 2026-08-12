# Instructions in a `@`-imported reference file silently never apply

**`~/.claude/CLAUDE.md` is a stow symlink into this repo, and Claude Code
resolves its `@references/...` imports relative to the symlink's *real target*
directory rather than `~/.claude/`, so an import only resolves if the file sits
next to the real `CLAUDE.md` inside this repo — and when it does not, the import
is skipped with no error.**

There is nothing to grep for when this happens. The import line is present in
the loaded instructions, the file exists, `readlink -f` resolves it, and the
guidance simply does not apply. A missing `@` import is silent by design, so a
typo'd path and a cross-repo path fail identically and invisibly.

The consequence that bites: `~/.claude/references/` is a real directory holding
per-file symlinks from *both* this repo and `dotfiles_local`. That flat layout
looks like it should make every reference importable from either side. It does
not. `@references/foo.md` in the public `CLAUDE.md` resolves to
`dotfiles/claude-code/.claude/references/foo.md`, never to
`~/.claude/references/foo.md`, so a file that lives only in `dotfiles_local` is
unreachable from the public `CLAUDE.md`.

This is also why private filenames ended up hardcoded in the public repo: the
public `CLAUDE.md` can only import paths that resolve inside the public repo, so
naming the private files there was the only thing that worked.

Ways past it:

- **Bridge the path.** Put a symlink at the location the import resolves to
  (inside the public repo) pointing at the private file, and gitignore it so the
  private path is never committed. `dotfiles_local`'s `inv stow` creates this via
  `_link_local_reference()`; `inv unstow` removes it. This keeps the public repo
  free of private filenames while the import still resolves.
- **Keep it in one repo.** An import whose target lives beside the real
  `CLAUDE.md` needs no bridge.

Do not trust a running agent's own context to confirm a fix here: a session
started before the edit keeps the old instructions, so it will report the old
state. Verify with a fresh subprocess asking for a fact only the imported file
contains:

```bash
cd /tmp && claude -p 'From your instructions only: <question only the import answers>' --max-turns 1
```

Ruled out along the way, so it is not re-derived: it is not that `@` imports
ignore symlinks (a symlinked reference file expands fine), not an import size
cap (a 14 KB import expands fine), and not the file mentioning its own path in
prose (a self-referential mention expands fine). The variable is solely whether
the path resolves next to the real `CLAUDE.md`.

**Confirmed:** 2026-08-11 against Claude Code on Linux, reproduced in an
isolated `HOME=/tmp/...` fixture where `~/.claude/CLAUDE.md` symlinked to a repo
elsewhere: the marker in a file beside the real target loaded, the marker in a
file in `~/.claude/references/` did not, and the subprocess reported the import
as listed but never expanded.
