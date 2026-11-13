"""Tests for the session adapters and digest rendering in harvest.py.

The skill ships beside its script rather than as an installed package, so
the import needs the path insert above it.
"""

# pylint: disable=missing-function-docstring,wrong-import-position

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

import harvest
from harvest import (
    LedgerEntry,
    commit_ledger,
    load_ledger,
    main,
    make_batches,
    plan_extract,
    read_claude,
)

FIX = Path(__file__).parent / "fixtures"


def _write_digest(path: Path, size: int, mtime: float) -> Path:
    """Create a digest-sized fixture file at `path` with its mtime pinned to `mtime`."""
    path.write_bytes(b"x" * size)
    os.utime(path, (mtime, mtime))
    return path


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


def test_discover_excludes_subagent_and_fork_transcripts_below_depth_one(tmp_path):
    # Depth 0 and depth 1 files (flat root, and <root>/<project>/<file>.jsonl)
    # are real top-level sessions and must be found. Deeper paths are the
    # subagent/fork transcripts pi and Claude nest under a session file
    # (pi: <dir>/<session>/<subagent-id>/run-0/session.jsonl; Claude:
    # <project>/<session-id>/subagents/x.jsonl) -- those must be excluded,
    # even though they parse as standalone sessions.
    claude_root = tmp_path / "claude"
    pi_root = tmp_path / "pi"

    (claude_root / "proj").mkdir(parents=True)
    (claude_root / "flat.jsonl").write_text("")  # depth 0
    (claude_root / "proj" / "top.jsonl").write_text("")  # depth 1
    (claude_root / "proj" / "sess-id" / "subagents").mkdir(parents=True)
    (claude_root / "proj" / "sess-id" / "subagents" / "x.jsonl").write_text("")  # depth 3

    (pi_root / "dir" / "sess" / "run-0").mkdir(parents=True)
    (pi_root / "dir" / "top.jsonl").write_text("")  # depth 1
    (pi_root / "dir" / "sess" / "run-0" / "session.jsonl").write_text("")  # depth 3
    (pi_root / "dir" / "sess" / "forks").mkdir(parents=True)
    (pi_root / "dir" / "sess" / "forks" / "fork.jsonl").write_text("")  # depth 3

    assert {p.name for p in harvest.discover(claude_root, pi_root)} == {
        "flat.jsonl",
        "top.jsonl",
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


def test_small_runs_get_one_batch(tmp_path):
    # total 200 KB -> 1 batch, no overflow
    digests = [
        _write_digest(tmp_path / f"claude__s{i}.md", 100_000, mtime=1_000 + i)
        for i in range(2)
    ]
    batches, overflow = make_batches(digests)
    assert batches == [digests]
    assert overflow == []


def test_batches_respect_cap_and_defer_newest(tmp_path):
    # 12 x 300 KB -> 8 batches; the 4 newest overflow
    digests = [
        _write_digest(tmp_path / f"claude__s{i}.md", 300_000, mtime=1_000 + i)
        for i in range(12)
    ]
    batches, overflow = make_batches(digests)
    assert len(batches) == 8
    assert {p for batch in batches for p in batch} == set(digests[:8])
    assert overflow == list(reversed(digests[8:]))


def test_one_oversized_digest_gets_its_own_batch(tmp_path):
    # one 900 KB plus two 100 KB -> the 900 KB file is alone
    big = _write_digest(tmp_path / "claude__big.md", 900_000, mtime=1_000)
    small_a = _write_digest(tmp_path / "claude__a.md", 100_000, mtime=1_001)
    small_b = _write_digest(tmp_path / "claude__b.md", 100_000, mtime=1_002)
    batches, overflow = make_batches([big, small_a, small_b])
    assert [big] in batches
    assert overflow == []
    other_batches = [batch for batch in batches if batch != [big]]
    assert {p for batch in other_batches for p in batch} == {small_a, small_b}


def test_batch_cli_writes_files_and_overflow_keys(tmp_path, capsys):
    # 12 x 300 KB digests, one with "__" inside its id, forces the same
    # 8-batches/4-overflow split as test_batches_respect_cap_and_defer_newest.
    run = tmp_path
    digests_dir = run / "digests"
    digests_dir.mkdir()
    names = [f"claude__s{i}.md" for i in range(11)] + ["claude__sess__with__dunder.md"]
    for i, name in enumerate(names):
        _write_digest(digests_dir / name, 300_000, mtime=1_000 + i)
    (run / "batch9.txt").write_text("stale\n")  # leftover from an earlier same-day run

    main(["batch", "--run-dir", str(run)])

    summary = json.loads(capsys.readouterr().out)
    assert summary["batches"] == 8
    assert summary["overflow_keys"] == [
        "claude:sess__with__dunder",
        "claude:s10",
        "claude:s9",
        "claude:s8",
    ]

    assert not (run / "batch9.txt").exists()
    batch0_paths = (run / "batch0.txt").read_text().splitlines()
    assert batch0_paths and all(Path(p).is_absolute() for p in batch0_paths)
    overflow_paths = (run / "overflow.txt").read_text().splitlines()
    assert len(overflow_paths) == 4 and all(Path(p).is_absolute() for p in overflow_paths)


def test_batch_cli_handles_empty_digests_dir(tmp_path, capsys):
    run = tmp_path
    (run / "digests").mkdir()

    main(["batch", "--run-dir", str(run)])

    summary = json.loads(capsys.readouterr().out)
    assert summary == {"batches": 0, "overflow_keys": []}
    assert list(run.glob("batch*.txt")) == []
    assert (run / "overflow.txt").read_text() == ""
