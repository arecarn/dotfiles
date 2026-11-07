"""Tests for detecting a uv.lock rewritten to a non-public package index."""

# Test names document each case.
# pylint: disable=missing-function-docstring

from manage import lockfile

PUBLIC = """\
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/ab/cd/x.tar.gz", hash = "sha256:00" }
"""


def test_a_lock_resolved_against_public_pypi_is_clean():
    assert lockfile.foreign_hosts(PUBLIC) == []


def test_a_rewritten_lock_reports_the_foreign_host_once():
    rewritten = PUBLIC.replace("pypi.org", "mirror.example.test").replace(
        "files.pythonhosted.org", "mirror.example.test"
    )

    assert lockfile.foreign_hosts(rewritten) == ["mirror.example.test"]


def test_a_foreign_host_among_public_ones_is_still_found():
    assert lockfile.foreign_hosts(
        PUBLIC + 'url = "https://internal.example.test/p/y.whl"\n'
    ) == ["internal.example.test"]
