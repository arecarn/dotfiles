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
from harvest import (
    LedgerEntry,
    commit_ledger,
    load_ledger,
    main,
    plan_extract,
    read_claude,
)

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


def test_plan_reads_only_new_messages():
    s = read_claude(FIX / "claude" / "basic.jsonl")
    assert plan_extract([s], {f"claude:{s.id}": LedgerEntry(harvested=2)}) == [(s, 2)]
    assert plan_extract([s], {f"claude:{s.id}": LedgerEntry(harvested=4)}) == []


def test_plan_restarts_a_session_that_shrank():
    s = read_claude(FIX / "claude" / "basic.jsonl")
    assert plan_extract([s], {f"claude:{s.id}": LedgerEntry(harvested=99)}) == [(s, 0)]


def test_plan_puts_deferred_sessions_first():
    old, new = read_claude(FIX / "claude" / "basic.jsonl"), read_claude(FIX / "claude" / "noise.jsonl")
    ledger = {f"claude:{new.id}": LedgerEntry(harvested=0, deferred=True)}
    assert [s.id for s, _ in plan_extract([old, new], ledger)][0] == new.id


def test_extract_leaves_the_ledger_until_commit(tmp_path):
    main(
        [
            "extract",
            "--state-dir",
            str(tmp_path),
            "--claude-root",
            str(FIX / "claude"),
            "--pi-root",
            str(FIX / "pi"),
        ]
    )
    assert not (tmp_path / "ledger.json").exists()
    run = next((tmp_path / "runs").iterdir())
    main(["commit", "--run-dir", str(run), "--state-dir", str(tmp_path)])
    assert load_ledger(tmp_path)  # now populated


def test_commit_with_deferred_keeps_old_offset(tmp_path):
    # Seed a ledger entry for the "basic" claude session, then run extract/commit
    # again with that session's key passed to --deferred: its harvested offset
    # must stay at the pre-run value while the other harvestable session (in
    # "second.jsonl") still advances to its full message count.
    s = read_claude(FIX / "claude" / "basic.jsonl")
    other = read_claude(FIX / "claude" / "second.jsonl")
    key = f"claude:{s.id}"
    other_key = f"claude:{other.id}"
    commit_ledger(tmp_path, {key: LedgerEntry(harvested=2)}, deferred=set())
    before = load_ledger(tmp_path)[key].harvested
    assert before == 2

    main(
        [
            "extract",
            "--state-dir",
            str(tmp_path),
            "--claude-root",
            str(FIX / "claude"),
            "--pi-root",
            str(FIX / "pi"),
        ]
    )
    run = next((tmp_path / "runs").iterdir())
    main(
        [
            "commit",
            "--run-dir",
            str(run),
            "--state-dir",
            str(tmp_path),
            "--deferred",
            key,
        ]
    )

    ledger = load_ledger(tmp_path)
    assert ledger[key].harvested == before
    assert ledger[key].deferred is True
    assert ledger[other_key].harvested == len(other.messages)
    assert ledger[other_key].deferred is False
