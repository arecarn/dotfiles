"""Tests for the session adapters and digest rendering in harvest.py.

The skill ships beside its script rather than as an installed package, so
the import needs the path insert above it.
"""

# pylint: disable=missing-function-docstring,wrong-import-position

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[1]))

import harvest
from harvest import (
    LedgerEntry,
    commit_ledger,
    entry_sources,
    load_ledger,
    main,
    make_batches,
    plan_extract,
    read_claude,
    resolve_source,
)

FIX = Path(__file__).parent / "fixtures"


def _write_digest(path: Path, size: int, mtime: float) -> Path:
    """Create a digest-sized fixture file at `path` with its mtime pinned to `mtime`."""
    path.write_bytes(b"x" * size)
    os.utime(path, (mtime, mtime))
    return path


def _run_git(args: list[str], cwd: Path) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True)


def _git_commit(repo: Path, message: str, date: str) -> None:
    """Commit the working tree's current state, with author and committer dates set to `date`."""
    _run_git(["add", "-A"], cwd=repo)
    env = dict(os.environ, GIT_AUTHOR_DATE=date, GIT_COMMITTER_DATE=date)
    subprocess.run(
        ["git", "commit", "-q", "-m", message], cwd=repo, check=True, capture_output=True, env=env
    )


@pytest.fixture(name="git_repo")
def _git_repo(tmp_path):
    """Build a repo with two dated commits to `src/a.cpp` and clone it so `origin/HEAD` resolves.

    The first commit lands 2026-01-01, the second (which re-touches
    `src/a.cpp`) lands 2026-07-01, so a `verified` date between the two
    shows one commit as stale and a `verified` date after both shows none.
    Returns the clone's path -- the thing a `repositories.yaml` `local:`
    entry would point at.
    """
    origin = tmp_path / "origin"
    origin.mkdir()
    _run_git(["init", "-q", "-b", "main"], cwd=origin)
    _run_git(["config", "user.email", "test@example.com"], cwd=origin)
    _run_git(["config", "user.name", "Test"], cwd=origin)

    (origin / "src").mkdir()
    (origin / "src" / "a.cpp").write_text("int a() { return 1; }\n")
    _git_commit(origin, "initial", "2026-01-01T00:00:00")

    (origin / "src" / "a.cpp").write_text("int a() { return 2; }\n")
    _git_commit(origin, "update a.cpp", "2026-07-01T00:00:00")

    clone = tmp_path / "repo"
    _run_git(["clone", "-q", str(origin), str(clone)], cwd=tmp_path)
    return clone


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
    old = read_claude(FIX / "claude" / "basic.jsonl")
    new = read_claude(FIX / "claude" / "noise.jsonl")
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
    assert not list(run.glob("batch*.txt"))
    assert (run / "overflow.txt").read_text() == ""


def _write_bundle_index(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / "index.md").write_text('---\nokf_version: "0.2"\n---\n# A bundle\n')


def test_discover_bundles_marks_privacy(tmp_path):
    knowledge_dir = tmp_path / "ai-knowledge"
    private_root = tmp_path / "private"
    _write_bundle_index(knowledge_dir / "public-bundle")
    _write_bundle_index(private_root / "stowed" / "private-bundle")
    (knowledge_dir / "private-bundle").symlink_to(private_root / "stowed" / "private-bundle")
    # A non-bundle entry (no okf_version) must be skipped.
    (knowledge_dir / "config.yaml").write_text("version: 1\n")

    bundles = {b.id: b for b in harvest.discover_bundles(knowledge_dir, private_root)}

    assert set(bundles) == {"public-bundle", "private-bundle"}
    assert bundles["public-bundle"].private is False
    assert bundles["private-bundle"].private is True


def test_entry_sources_reads_verified_and_list(tmp_path):
    md = tmp_path / "entry.md"
    md.write_text(
        '---\n'
        'type: Reference\n'
        'verified: "2026-10-06"\n'
        'sources:\n'
        '  - "RepoA origin/develop deadbeef: a.cpp, b.cpp"\n'
        "  - 'RepoB abc123: c.cpp'\n"
        "---\n"
        "# Body\n"
    )

    verified, sources = entry_sources(md)

    assert verified == "2026-10-06"
    assert sources == [
        "RepoA origin/develop deadbeef: a.cpp, b.cpp",
        "RepoB abc123: c.cpp",
    ]


def test_entry_sources_handles_missing_verified(tmp_path):
    md = tmp_path / "entry.md"
    md.write_text("---\ntype: Reference\nstatus: active\n---\n# Body\n")

    verified, sources = entry_sources(md)

    assert verified is None
    assert not sources


def test_resolve_source_finds_repo_and_files(git_repo):
    resolved = resolve_source("RepoA origin/develop deadbeef: src/a.cpp", {"RepoA": git_repo})

    assert resolved is not None
    repo_root, files = resolved
    assert repo_root == git_repo
    assert files == ["src/a.cpp"]


def test_resolve_source_finds_a_bare_filename_at_any_depth(git_repo):
    resolved = resolve_source("RepoA origin/develop deadbeef: a.cpp", {"RepoA": git_repo})

    assert resolved is not None
    _repo_root, files = resolved
    assert files == ["src/a.cpp"]


def test_resolve_source_returns_none_for_dng_and_unknown_repo(git_repo):
    assert resolve_source("DNG module 357062: ASI", {"Repo": git_repo}) is None
    assert resolve_source("OtherRepo origin/develop: x.cpp", {"Repo": git_repo}) is None


def test_resolve_source_prefers_the_longest_matching_name(git_repo):
    # "RepoA" must not match inside the text naming "RepoAB" -- a shorter
    # repo name sharing a prefix should lose to the longer, correct match.
    repo_paths = {"RepoA": git_repo, "RepoAB": git_repo}
    resolved = resolve_source("RepoAB origin/develop: src/a.cpp", repo_paths)
    assert resolved is not None


def test_stale_lists_commits_after_verified(tmp_path, git_repo):
    knowledge_dir = tmp_path / "ai-knowledge"
    private_root = tmp_path / "private"
    bundle = knowledge_dir / "bundle"
    _write_bundle_index(bundle)
    (bundle / "repositories.yaml").write_text(
        "repositories:\n"
        "- name: RepoA\n"
        "  path: group/RepoA\n"
        "  local: repo\n"
    )
    # verified between the two commits: only the 2026-07-01 commit is stale.
    (bundle / "entry.md").write_text(
        '---\n'
        'verified: "2026-06-01"\n'
        "sources:\n"
        '  - "RepoA deadbeef: src/a.cpp"\n'
        "---\n"
        "# Body\n"
    )
    # verified after both commits: nothing stale for this entry.
    (bundle / "settled.md").write_text(
        '---\n'
        'verified: "2026-08-01"\n'
        "sources:\n"
        '  - "RepoA deadbeef: src/a.cpp"\n'
        "---\n"
        "# Body\n"
    )

    # git_repo is already the clone at tmp_path/"repo", matching repositories.yaml's "local: repo".
    assert git_repo == tmp_path / "repo"
    workspace_root = tmp_path

    report = harvest.stale(knowledge_dir, private_root, [workspace_root], fetch=False)

    assert "entry.md" in report
    assert "1 commits" in report
    assert "settled.md" not in report
    assert "Unresolved sources: 0" in report


def test_stale_counts_a_repo_with_no_origin_head_as_unresolved(tmp_path):
    # A repo with no remote has no origin/HEAD, so `git log ... origin/HEAD`
    # fails: the source must be counted unresolved, not crash and not show
    # up as "0 commits".
    repo = tmp_path / "repo"
    repo.mkdir()
    _run_git(["init", "-q", "-b", "main"], cwd=repo)
    _run_git(["config", "user.email", "test@example.com"], cwd=repo)
    _run_git(["config", "user.name", "Test"], cwd=repo)
    (repo / "a.cpp").write_text("int a() { return 1; }\n")
    _git_commit(repo, "initial", "2026-01-01T00:00:00")

    knowledge_dir = tmp_path / "ai-knowledge"
    private_root = tmp_path / "private"
    bundle = knowledge_dir / "bundle"
    _write_bundle_index(bundle)
    (bundle / "repositories.yaml").write_text(
        "repositories:\n- name: RepoA\n  path: group/RepoA\n  local: repo\n"
    )
    (bundle / "entry.md").write_text(
        '---\nverified: "2026-01-01"\nsources:\n  - "RepoA deadbeef: a.cpp"\n---\n# Body\n'
    )

    report = harvest.stale(knowledge_dir, private_root, [tmp_path], fetch=False)

    assert "May be stale" in report
    assert "0 commits" not in report
    assert "entry.md" not in report
    assert "Unresolved sources: 1" in report


def test_stale_fetches_each_repo_at_most_once(monkeypatch, tmp_path, git_repo):
    # Two entries in two different bundles cite the same repo; fetch must
    # run once per `stale()` call, not once per resolved sources entry.
    fetch_calls = []
    real_run = harvest.subprocess.run

    def counting_run(args, **kwargs):
        if args[:2] == ["git", "fetch"]:
            fetch_calls.append(args)
        check = kwargs.pop("check", False)
        return real_run(args, check=check, **kwargs)

    monkeypatch.setattr(harvest.subprocess, "run", counting_run)

    knowledge_dir = tmp_path / "ai-knowledge"
    private_root = tmp_path / "private"
    repositories_yaml = "repositories:\n- name: RepoA\n  path: group/RepoA\n  local: repo\n"
    source_entry = (
        '---\nverified: "2026-01-01"\nsources:\n  - "RepoA deadbeef: a.cpp"\n---\n# Body\n'
    )

    first = knowledge_dir / "first"
    _write_bundle_index(first)
    (first / "repositories.yaml").write_text(repositories_yaml)
    (first / "entry.md").write_text(source_entry)

    second = knowledge_dir / "second"
    _write_bundle_index(second)
    (second / "entry.md").write_text(source_entry)

    workspace_root = tmp_path  # git_repo fixture clones to tmp_path / "repo"
    assert git_repo == tmp_path / "repo"

    harvest.stale(knowledge_dir, private_root, [workspace_root], fetch=True)

    assert len(fetch_calls) == 1
