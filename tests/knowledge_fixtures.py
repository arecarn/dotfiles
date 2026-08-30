"""Bundle fixtures shared by the CLI and hook tests.

Both drive the same integration from outside -- one through the launcher, one
through the SessionStart hook -- so they need the same bundle on disk. Kept here
rather than duplicated, since the shape encodes the contract: a bundle is a
directory beside the config file, not a declaration inside it.
"""

INDEX = """\
---
okf_version: "0.2"
---
# Personal knowledge

* [Ops](ops.md) - operations
"""


def bundle(root, index=INDEX):
    """Write a minimal OKF bundle at `root` and return it."""
    root.mkdir(parents=True, exist_ok=True)
    (root / "index.md").write_text(index, encoding="utf-8")
    return root


def config_dir(tmp_path, bundle_root):
    """A config directory holding `bundle_root` as the bundle "personal".

    Linked in rather than declared: a directory beside the config file is a
    bundle, so these tests write no config file at all.
    """
    directory = tmp_path / "config"
    directory.mkdir(exist_ok=True)
    link = directory / "personal"
    if not link.exists():
        link.symlink_to(bundle_root)
    return directory
