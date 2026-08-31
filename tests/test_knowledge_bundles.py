"""Tests for the knowledge bundle structure check.

The drifts this guards against were both found by agents doing real work, which
is the expensive way to catch a typo. Each negative case here is one of those,
reduced: a link that stopped resolving, and an index entry that stopped matching
the document it routes to.
"""

import pathlib
import textwrap

from manage.knowledge import bundles

INDEX = """\
---
okf_version: "0.2"
---
# Test knowledge

* [Widgets](widgets.md) - making a widget, and the one that bites
"""

CONCEPT = """\
---
type: Reference
title: Widgets
description: Making a widget, and the one that bites
---
# Widgets

Body.
"""


def _bundle(tmp_path, index=INDEX, concept=CONCEPT):
    """A repo root holding one project bundle."""
    root = tmp_path / "repo"
    knowledge = root / "agents-knowledge"
    knowledge.mkdir(parents=True)
    (knowledge / "index.md").write_text(index, encoding="utf-8")
    if concept is not None:
        (knowledge / "widgets.md").write_text(concept, encoding="utf-8")
    return root


def test_clean_bundle_has_no_problems(tmp_path):
    """An index and a concept that agree produce nothing."""
    assert not bundles.check(_bundle(tmp_path))


def test_this_repo_is_clean():
    """The check must pass on the bundles it was written for."""
    assert not bundles.check(pathlib.Path(__file__).resolve().parent.parent)


def test_broken_link_is_reported(tmp_path):
    """A link to a document that is not there costs a wasted read."""
    root = _bundle(tmp_path, concept=None)
    problems = bundles.check(root)
    assert any("does not resolve" in p for p in problems)


def test_description_drift_is_reported(tmp_path):
    """An index entry that no longer says what its document says."""
    drifted = CONCEPT.replace(
        "description: Making a widget, and the one that bites",
        "description: Making a widget, and why it never fails the build",
    )
    problems = bundles.check(_bundle(tmp_path, concept=drifted))
    assert any("does not match its description field" in p for p in problems)


def test_presentation_differences_are_not_drift(tmp_path):
    """Backticks, case, wrapping, and a trailing period are not drift."""
    index = INDEX.replace(
        "* [Widgets](widgets.md) - making a widget, and the one that bites",
        "* [Widgets](widgets.md) - Making a `widget`, and\n  the one that bites.",
    )
    assert not bundles.check(_bundle(tmp_path, index=index))


def test_missing_frontmatter_field_is_reported(tmp_path):
    """The frontmatter a reader is shown must be present."""
    stripped = CONCEPT.replace("type: Reference\n", "")
    problems = bundles.check(_bundle(tmp_path, concept=stripped))
    assert any("frontmatter missing type" in p for p in problems)


def test_orphan_concept_is_reported(tmp_path):
    """A document no index links to is a document no model will ever see."""
    root = _bundle(tmp_path)
    (root / "agents-knowledge" / "orphan.md").write_text(
        CONCEPT.replace("Widgets", "Orphan"), encoding="utf-8"
    )
    problems = bundles.check(root)
    assert any("not linked from any index" in p for p in problems)


def test_links_out_of_the_bundle_only_need_to_exist(tmp_path):
    """A pointer to docs/adr/ keeps its own conventions; only existence is ours."""
    root = _bundle(tmp_path)
    (root / "docs").mkdir()
    (root / "docs" / "adr").mkdir()
    index = root / "agents-knowledge" / "index.md"
    index.write_text(
        INDEX + "* [Decisions](../docs/adr/) - the calls that were made\n",
        encoding="utf-8",
    )
    assert not bundles.check(root)


def test_a_directory_without_a_version_marker_is_not_a_bundle(tmp_path):
    """No `okf_version` means not a bundle, so nothing in it is checked."""
    root = tmp_path / "repo"
    knowledge = root / "agents-knowledge"
    knowledge.mkdir(parents=True)
    (knowledge / "index.md").write_text("# Not a bundle\n", encoding="utf-8")
    (knowledge / "widgets.md").write_text("no frontmatter\n", encoding="utf-8")
    assert not bundles.repo_bundles(root)
    assert not bundles.check(root)


def test_personal_bundles_are_checked_too(tmp_path):
    """A stowed personal bundle is ours, and drifts the same way."""
    root = tmp_path / "repo"
    personal = root / "agents" / ".config" / "ai-knowledge" / "personal"
    personal.mkdir(parents=True)
    (personal / "index.md").write_text(INDEX, encoding="utf-8")
    (personal / "widgets.md").write_text(
        CONCEPT.replace("description: Making a widget, and the one that bites",
                        "description: Something else entirely"),
        encoding="utf-8",
    )
    problems = bundles.check(root)
    assert any("does not match its description field" in p for p in problems)
    assert any("personal" in p for p in problems)


def test_wrapped_multi_entry_index_parses_each_entry(tmp_path):
    """Real indexes wrap; a parser that only reads one line would pass falsely."""
    root = tmp_path / "repo"
    knowledge = root / "agents-knowledge"
    knowledge.mkdir(parents=True)
    (knowledge / "index.md").write_text(
        textwrap.dedent("""\
            ---
            okf_version: "0.2"
            ---
            # Test knowledge

            * [Widgets](widgets.md) - making a widget, and
              the one that bites
            * [Gadgets](gadgets.md) - making a gadget, and
              the one that bites harder
            """),
        encoding="utf-8",
    )
    (knowledge / "widgets.md").write_text(CONCEPT, encoding="utf-8")
    (knowledge / "gadgets.md").write_text(
        CONCEPT.replace("Widgets", "Gadgets").replace(
            "description: Making a widget, and the one that bites",
            "description: Making a gadget, and something unrelated",
        ),
        encoding="utf-8",
    )
    problems = bundles.check(root)
    assert len(problems) == 1
    assert "gadgets.md" in problems[0]


def test_headings_inside_code_fences_do_not_count(tmp_path):
    """A make sample is full of `#` comments; none of them is a heading."""
    unstructured = CONCEPT.replace(
        "# Widgets\n\nBody.\n",
        "Prose with no heading.\n\n```make\n# makefile\n# Detect the container\n```\n",
    )
    problems = bundles.check(_bundle(tmp_path, concept=unstructured))
    assert any("no Markdown heading outside code fences" in p for p in problems)


def test_a_real_heading_after_a_code_fence_counts(tmp_path):
    """Fence tracking must resume, not swallow the rest of the file."""
    structured = CONCEPT.replace(
        "# Widgets\n\nBody.\n",
        "Prose first.\n\n```make\n# makefile\n```\n\n# Widgets\n\nBody.\n",
    )
    assert not bundles.check(_bundle(tmp_path, concept=structured))
