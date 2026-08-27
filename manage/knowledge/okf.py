"""Reading just enough of an OKF bundle to discover and disclose it.

Deliberately shallow. This module answers two questions -- "does this look like a
bundle we support?" and "what does its root index say?" -- and leaves conformance
to OKF's own tooling, which nothing here has been checked against. The
bundle-root `index.md` is where the spec puts `okf_version`, which makes it the
discovery marker: without it, an `agents-knowledge/` directory is just a
directory.

Bundle contents are untrusted input. Index text is returned verbatim for the
renderer to frame, never parsed for instructions and never executed.
"""

import pathlib
import re

INDEX_NAME = "index.md"
SUPPORTED_VERSION = "0.2"

MAX_INDEX_BYTES = 256 * 1024

_FRONTMATTER = re.compile(r"\A---\r?\n(.*?)\r?\n---\r?(?:\n|\Z)", re.DOTALL)
# Matched as text rather than parsed as YAML: the version must be the *string*
# "0.2", and a YAML load would silently accept the float 0.2 as equal.
_VERSION = re.compile(r'^okf_version:\s*"([^"]*)"\s*$', re.MULTILINE)


def read_index(bundle_root):
    """The root index text of an OKF bundle, or None when unusable.

    None covers every "not a bundle we can use" case -- absent, a directory, not
    a regular file, oversized, undecodable, no frontmatter, or an unsupported
    version -- because callers treat them identically: the bundle is skipped.
    """
    index = pathlib.Path(bundle_root) / INDEX_NAME
    try:
        if not index.is_file():
            return None
        if index.stat().st_size > MAX_INDEX_BYTES:
            return None
        text = index.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None

    match = _FRONTMATTER.match(text)
    if not match:
        return None
    version = _VERSION.search(match.group(1))
    if not version or version.group(1) != SUPPORTED_VERSION:
        return None
    return text


def is_bundle(bundle_root):
    """Whether `bundle_root` holds a readable, supported OKF root index."""
    return read_index(bundle_root) is not None
