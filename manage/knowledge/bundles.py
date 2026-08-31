"""Checking this repo's own knowledge bundles for the drifts that cost a read.

A bundle's index is the only thing a model sees, so its entry descriptions are
what decide whether a document is opened. Two failures make that decision wrong
and neither shows up in any other linter: a link that no longer resolves, and an
entry whose description no longer says what its document says. Both were found
by hand, by agents using the bundle for real work, which is too expensive a way
to catch a typo.

This checks structure only. Whether a document is *true* is not checkable here
-- that needs someone who reads the source it describes.
"""

import pathlib
import re

from manage.knowledge import okf

# A bundle entry is a Markdown bullet holding one link and a description after a
# dash, wrapped across as many lines as it needs:
#
#     * [Pi configuration](pi.md) - what lives in `pi/.pi/agent/`, and the fold
#       barrier a package with its own config must get
_ENTRY = re.compile(
    r"^\*\s+\[(?P<title>[^\]]+)\]\((?P<target>[^)]+)\)"
    r"(?:\s*[-–—]\s*(?P<description>.*?))?"
    r"(?=\n\*|\n#|\n\n|\Z)",
    re.MULTILINE | re.DOTALL,
)

REQUIRED_FIELDS = ("type", "title", "description")


def _normalize(text):
    """Compare descriptions on wording alone.

    Backticks, case, line wrapping, and a trailing period are presentation: an
    index line and a frontmatter field may legitimately differ in all four while
    saying the same thing. Anything else differing is drift.
    """
    return " ".join((text or "").replace("`", "").split()).lower().rstrip(".")


def repo_bundles(repo_root):
    """Every OKF bundle this repo owns, root index first.

    Both places a bundle can live here: the project's own `agents-knowledge/`,
    and the personal bundles stowed from `agents/.config/ai-knowledge/`. A work
    bundle is deliberately not reachable -- it lives in a `dotfiles_local`
    checkout and is not ours to check.
    """
    repo_root = pathlib.Path(repo_root)
    candidates = [repo_root / "agents-knowledge"]
    stowed = repo_root / "agents" / ".config" / "ai-knowledge"
    if stowed.is_dir():
        candidates.extend(sorted(p for p in stowed.iterdir() if p.is_dir()))
    return [p for p in candidates if okf.is_bundle(p)]


def _indexes(bundle):
    return sorted(bundle.rglob(okf.INDEX_NAME))


def _check_entry(index, entry, bundle, problems, linked):
    """One index entry: does its target exist, and still say what it promises?"""
    target = entry.group("target")
    if "://" in target:
        return
    resolved = (index.parent / target).resolve()
    if not resolved.exists():
        problems.append(f"{index}: link to {target} does not resolve")
        return

    if resolved.is_dir() or resolved.suffix != ".md":
        return
    if bundle.resolve() not in resolved.parents:
        # A link out to docs/adr/ or docs/gotchas/ is a pointer to material that
        # keeps its own conventions; only its existence is ours to check.
        return

    linked.add(resolved)
    described = okf.read_field(resolved.read_text(encoding="utf-8"), "description")
    index_text = entry.group("description")
    if index_text is None:
        problems.append(f"{index}: entry for {target} has no description")
        return
    if _normalize(described) != _normalize(index_text):
        problems.append(
            f"{index}: entry for {target} does not match its description field\n"
            f"    index: {_normalize(index_text)}\n"
            f"    file:  {_normalize(described)}"
        )


def check(repo_root):
    """Structural problems across this repo's bundles, as printable strings.

    Empty means every index link resolves, every concept carries the frontmatter
    a reader is shown, no concept is unreachable from an index, and no entry
    describes its document differently than the document describes itself.
    """
    problems = []
    for bundle in repo_bundles(repo_root):
        linked = set()
        indexes = _indexes(bundle)
        for index in indexes:
            text = index.read_text(encoding="utf-8")
            body = text[len(okf.read_frontmatter(text) or "") :]
            for entry in _ENTRY.finditer(body):
                _check_entry(index, entry, bundle, problems, linked)

        for concept in sorted(bundle.rglob("*.md")):
            if concept.name == okf.INDEX_NAME:
                continue
            if concept.resolve() not in linked:
                problems.append(f"{concept}: not linked from any index")
            content = concept.read_text(encoding="utf-8")
            missing = [f for f in REQUIRED_FIELDS if not okf.read_field(content, f)]
            if missing:
                problems.append(f"{concept}: frontmatter missing {', '.join(missing)}")
    return problems
