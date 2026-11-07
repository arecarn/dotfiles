"""Check that `uv.lock` names only the public package index.

A machine configured against an internal index makes `uv run` rewrite every URL
in the lockfile to that host (docs/gotchas/uv-run-rewrites-uv-lock-to-an-internal-registry.md).
This repo is public, so the lock must never be committed in that state.
"""

import re

# Hosts a lock resolved against public PyPI contains: the index and its file CDN.
PUBLIC_HOSTS = frozenset({"pypi.org", "files.pythonhosted.org"})

_HOST = re.compile(r"https?://([^/\s\"']+)")


def foreign_hosts(text):
    """Hosts in `text` that are not public PyPI, sorted."""
    return sorted({h for h in _HOST.findall(text) if h not in PUBLIC_HOSTS})
