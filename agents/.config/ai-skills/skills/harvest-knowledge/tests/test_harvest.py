"""Tests for the session adapters and digest rendering in harvest.py.

The skill ships beside its script rather than as an installed package, so
the import needs the path insert above it.
"""

# pylint: disable=missing-function-docstring,wrong-import-position

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

import harvest

FIX = Path(__file__).parent / "fixtures"


def test_read_claude_keeps_text_and_drops_tool_output():
    s = harvest.read_claude(FIX / "claude" / "basic.jsonl")
    assert s.source == "claude" and s.cwd == "/work/repo"
    assert [m.role for m in s.messages] == ["user", "assistant", "user", "assistant"]
    assert all("TOOL_RESULT_SENTINEL" not in m.text for m in s.messages)


def test_read_claude_skips_meta_sidechain_and_command_wrappers():
    s = harvest.read_claude(FIX / "claude" / "noise.jsonl")
    assert all(not m.text.startswith("<command") for m in s.messages)
    assert "SIDECHAIN_SENTINEL" not in " ".join(m.text for m in s.messages)


def test_read_claude_tolerates_a_truncated_last_line():
    s = harvest.read_claude(FIX / "claude" / "truncated.jsonl")
    assert len(s.messages) == 2


def test_read_pi_keeps_user_and_assistant_only():
    s = harvest.read_pi(FIX / "pi" / "basic.jsonl")
    assert s.source == "pi" and s.id == "pi-session-1" and s.cwd == "/work/pi"
    assert [m.role for m in s.messages] == ["user", "assistant"]


def test_not_harvestable_when_self_tagged_tmp_or_short():
    assert not harvest.is_harvestable(harvest.read_claude(FIX / "claude" / "self_tagged.jsonl"))
    assert not harvest.is_harvestable(harvest.read_claude(FIX / "claude" / "tmp_cwd.jsonl"))
    assert not harvest.is_harvestable(harvest.read_claude(FIX / "claude" / "one_exchange.jsonl"))
    assert harvest.is_harvestable(harvest.read_claude(FIX / "claude" / "basic.jsonl"))


def test_render_digest_starts_at_offset_and_caps_each_message():
    s = harvest.read_claude(FIX / "claude" / "basic.jsonl")
    d = harvest.render_digest(s, start=2, cap=20)
    assert d.startswith(f"# session {s.id} source=claude cwd=/work/repo")
    assert d.count("USER: ") == 1 and d.count("ASSISTANT: ") == 1
    assert all(len(line) <= len("ASSISTANT: ") + 20 for line in d.splitlines()[1:] if line)


def test_discover_finds_both_layouts(tmp_path):
    (tmp_path / "c" / "proj").mkdir(parents=True)
    (tmp_path / "c" / "proj" / "a.jsonl").write_text("")
    (tmp_path / "p" / "--x--").mkdir(parents=True)
    (tmp_path / "p" / "--x--" / "b.jsonl").write_text("")
    assert {p.name for p in harvest.discover(tmp_path / "c", tmp_path / "p")} == {
        "a.jsonl",
        "b.jsonl",
    }
