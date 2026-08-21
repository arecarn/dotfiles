# `clean-stow` removes no dead links on Windows, silently

**On Windows, `Path.readlink()` returns the symlink's substitute name with an
extended-length prefix — `\\?\C:\...` rather than `C:\...`. Any path built from
it compares unequal to a path built normally, so a containment check like
`repo_dir in target.parents` is always False and the sweep removes nothing.**

Nothing errors. `inv clean-stow` exits 0 having done no work, which is
indistinguishable from a home directory that had no dead links in it. The same
comparison works on Linux and macOS, so a local run proves nothing here.

The prefix appears in two forms: `\\?\` and, for the NT object path,
`\??\`. Strip either before building a path to compare — `manage.stow`
does this in `_strip_extended_prefix`, called from `_link_target`.

`Path.resolve()` does not remove the prefix, so resolving both sides is not a
fix. Neither is comparing resolved paths: the prefix survives resolution.

Caught by `tests/test_stow.py`, whose dead-link tests failed on the Windows CI
leg while passing on Linux. The prefix-stripping tests beside them are pure
string operations and run everywhere, but only the Windows leg exercises the
`readlink()` behaviour that produces the prefix in the first place.

**Confirmed:** 2026-08-20, against Windows CI (`windows-latest`) on GitHub
Actions, Python 3.14.
