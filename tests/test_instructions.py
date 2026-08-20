# pylint: disable=missing-function-docstring,use-implicit-booleaness-not-comparison,unused-import
"""Tests for the shared-instruction generator."""

import pathlib

import pytest

import instructions


@pytest.fixture(name="fragment_dir")
def fixture_fragment_dir(tmp_path):
    """A fragment directory with two fragments and a manifest."""
    frags = tmp_path / "fragments"
    frags.mkdir()
    (frags / "alpha.md").write_text("### Alpha\n\nFirst fragment.\n")
    (frags / "beta.md").write_text("### Beta\n\nSecond fragment.\n")
    (frags / "manifest.yaml").write_text(
        "outputs:\n"
        "  out/one.md:\n"
        "    fragments: [alpha, beta]\n"
        "  out/two.md:\n"
        "    fragments: [alpha]\n"
        "  out/styled.md:\n"
        "    header: |\n"
        "      ---\n"
        "      name: Styled\n"
        "      ---\n"
        "    fragments: [alpha]\n"
    )
    return frags


def test_load_manifest_maps_outputs_to_fragment_lists(fragment_dir):
    manifest = instructions.load_manifest(fragment_dir / "manifest.yaml")
    assert manifest["out/one.md"] == instructions.Output(["alpha", "beta"])
    assert manifest["out/two.md"] == instructions.Output(["alpha"])


def test_load_manifest_carries_an_output_header(fragment_dir):
    manifest = instructions.load_manifest(fragment_dir / "manifest.yaml")
    assert manifest["out/styled.md"].header == "---\nname: Styled\n---\n"
    assert manifest["out/one.md"].header is None


def test_render_output_puts_the_header_before_the_banner(fragment_dir):
    text = instructions.render_output(["alpha"], fragment_dir, header="---\nname: S\n---\n")
    assert text.startswith("---\nname: S\n---\n\n<!--")
    assert text.index("gen-instructions") < text.index("First fragment.")


def test_render_output_concatenates_fragments_in_order(fragment_dir):
    text = instructions.render_output(["alpha", "beta"], fragment_dir)
    assert text.index("First fragment.") < text.index("Second fragment.")


def test_render_output_starts_with_a_generated_file_banner(fragment_dir):
    text = instructions.render_output(["alpha"], fragment_dir)
    assert text.startswith("<!--")
    assert "gen-instructions" in text
    assert "alpha.md" in text


def test_generate_writes_every_output(tmp_path, fragment_dir, monkeypatch):
    monkeypatch.chdir(tmp_path)
    drift = instructions.generate(
        manifest_path=fragment_dir / "manifest.yaml", fragment_dir=fragment_dir
    )
    assert drift == []
    assert "First fragment." in (tmp_path / "out" / "one.md").read_text()
    assert "Second fragment." not in (tmp_path / "out" / "two.md").read_text()
    assert (tmp_path / "out" / "styled.md").read_text().startswith("---\nname: Styled\n---\n")


def test_check_reports_no_drift_after_generate(tmp_path, fragment_dir, monkeypatch):
    monkeypatch.chdir(tmp_path)
    instructions.generate(
        manifest_path=fragment_dir / "manifest.yaml", fragment_dir=fragment_dir
    )
    drift = instructions.generate(
        check=True, manifest_path=fragment_dir / "manifest.yaml", fragment_dir=fragment_dir
    )
    assert drift == []


def test_check_reports_drift_when_a_fragment_changed(tmp_path, fragment_dir, monkeypatch):
    monkeypatch.chdir(tmp_path)
    instructions.generate(
        manifest_path=fragment_dir / "manifest.yaml", fragment_dir=fragment_dir
    )
    (fragment_dir / "alpha.md").write_text("### Alpha\n\nEdited.\n")
    drift = instructions.generate(
        check=True, manifest_path=fragment_dir / "manifest.yaml", fragment_dir=fragment_dir
    )
    assert drift == ["out/one.md", "out/two.md", "out/styled.md"]


def test_check_does_not_write_files(tmp_path, fragment_dir, monkeypatch):
    monkeypatch.chdir(tmp_path)
    drift = instructions.generate(
        check=True, manifest_path=fragment_dir / "manifest.yaml", fragment_dir=fragment_dir
    )
    assert drift == ["out/one.md", "out/two.md", "out/styled.md"]
    assert not (tmp_path / "out").exists()


def test_render_seam_is_applied_to_each_fragment(fragment_dir, monkeypatch):
    monkeypatch.setattr(instructions, "_render", lambda text: text.upper())
    text = instructions.render_output(["alpha"], fragment_dir)
    assert "FIRST FRAGMENT." in text
