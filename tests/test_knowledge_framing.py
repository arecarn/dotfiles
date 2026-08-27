"""Tests for generating the adapters' copy of the catalog framing.

The framing is the one structural control over untrusted index text and it exists
in two languages, so it is generated rather than copied. These pin the generator's
contract: byte-identical constants, and output biome accepts unchanged.
"""

# Test names document each case, and the helpers are private to the module.
# pylint: disable=missing-function-docstring

import json
import subprocess

from manage.knowledge import framing, resolver

BIOME = "node_modules/.bin/biome"


def test_the_generated_module_carries_the_resolver_constants():
    text = framing.render()

    assert json.dumps(resolver.BEGIN_MARKER) in text
    assert json.dumps(resolver.END_MARKER) in text
    assert json.dumps(resolver.PREAMBLE) in text
    assert f"randomBytes({resolver.FENCE_BYTES})" in text


def test_an_apostrophe_in_the_preamble_survives():
    """The preamble says "the user's requests"; a quote-swapping generator would
    corrupt that into `user"s` and break the string."""
    assert "user's requests" in resolver.PREAMBLE
    assert "user's requests" in framing.render()


def test_the_generated_module_is_already_formatted(tmp_path):
    """inv lint runs biome over every .ts file, generated ones included, so a
    generator that emits unformatted text fails the lint it cannot fix."""
    biome = framing.pathlib.Path(BIOME)
    if not biome.exists():
        return  # toolchain not installed; lint_typescript reports that itself

    candidate = tmp_path / "framing.ts"
    candidate.write_text(framing.render(), encoding="utf-8")

    done = subprocess.run(
        [str(biome.resolve()), "format", str(candidate)],
        capture_output=True,
        text=True,
        check=False,
    )

    assert done.returncode == 0, done.stdout + done.stderr


def test_check_reports_drift_without_writing(tmp_path):
    target = tmp_path / "framing.ts"
    target.write_text("// stale\n", encoding="utf-8")

    code = framing.generate(check=True, target=target)

    assert code == 1
    assert target.read_text(encoding="utf-8") == "// stale\n"


def test_generating_twice_writes_the_same_bytes(tmp_path):
    target = tmp_path / "framing.ts"

    framing.generate(target=target)
    first = target.read_text(encoding="utf-8")
    framing.generate(target=target)

    assert target.read_text(encoding="utf-8") == first
    assert framing.generate(check=True, target=target) == 0
