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


def _write_jsonl(path: Path, records: list[dict]) -> Path:
    """Write `records` as one JSON object per line to `path`, creating its directory."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r) + "\n" for r in records), encoding="utf-8")
    return path


def _claude_session(path: Path, user_texts: list[str], cwd: str = "/work/repo") -> Path:
    """Write a Claude session alternating each of `user_texts` with a fixed assistant reply."""
    records = []
    for text in user_texts:
        records.append({"type": "user", "cwd": cwd, "message": {"content": text}})
        records.append(
            {
                "type": "assistant",
                "cwd": cwd,
                "message": {"content": [{"type": "text", "text": "Reply."}]},
            }
        )
    return _write_jsonl(path, records)


def _pi_session(path: Path, session_id: str, user_texts: list[str]) -> Path:
    """Write a pi session alternating each of `user_texts` with a fixed assistant reply."""
    records: list[dict] = [{"type": "session", "id": session_id, "cwd": "/work/pi"}]
    for text in user_texts:
        for role, body in (("user", text), ("assistant", "Reply.")):
            records.append(
                {
                    "type": "message",
                    "message": {
                        "role": role,
                        "content": [{"type": "text", "text": body}],
                    },
                }
            )
    return _write_jsonl(path, records)


def _extract(state: Path, claude_root: Path, pi_root: Path) -> Path:
    """Run the `extract` CLI and return the run dir it wrote."""
    main(
        [
            "extract",
            "--state-dir",
            str(state),
            "--claude-root",
            str(claude_root),
            "--pi-root",
            str(pi_root),
        ]
    )
    return next((state / "runs").iterdir())


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
    assert not overflow


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
    assert not overflow
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
    assert resolve_source("DNG module 123456: Example spec", {"Repo": git_repo}) is None
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


def test_commit_reads_overflow_file_and_rejects_unknown_deferred_keys(tmp_path, capsys):
    state = tmp_path / "state"
    claude_root = tmp_path / "claude"
    _claude_session(claude_root / "proj" / "kept.jsonl", ["First ask.", "Second ask."])
    _claude_session(claude_root / "proj" / "over.jsonl", ["Other ask.", "Follow-up."])
    run = _extract(state, claude_root, tmp_path / "pi")
    (run / "overflow.txt").write_text(f"{(run / 'digests' / 'claude__over.md').resolve()}\n")

    # A typo'd key is refused, and nothing reaches the ledger.
    status = main(
        [
            "commit",
            "--run-dir",
            str(run),
            "--state-dir",
            str(state),
            "--deferred",
            "claude:typo",
        ]
    )
    assert status != 0
    assert "claude:typo" in capsys.readouterr().err
    assert not (state / "ledger.json").exists()

    # With no --deferred at all, overflow.txt alone defers the overflow session.
    assert main(["commit", "--run-dir", str(run), "--state-dir", str(state)]) == 0
    ledger = load_ledger(state)
    assert ledger["claude:over"] == LedgerEntry(harvested=0, deferred=True)
    assert ledger["claude:kept"] == LedgerEntry(harvested=4, deferred=False)


def test_commit_defer_batch_defers_every_key_in_that_batch(tmp_path):
    state = tmp_path / "state"
    claude_root = tmp_path / "claude"
    for name in ("a", "b", "c"):
        _claude_session(claude_root / "proj" / f"{name}.jsonl", [f"Ask {name}.", "More."])
    run = _extract(state, claude_root, tmp_path / "pi")
    digests = run / "digests"
    (run / "batch0.txt").write_text(f"{(digests / 'claude__a.md').resolve()}\n")
    (run / "batch1.txt").write_text(
        f"{(digests / 'claude__b.md').resolve()}\n{(digests / 'claude__c.md').resolve()}\n"
    )

    status = main(
        [
            "commit",
            "--run-dir",
            str(run),
            "--state-dir",
            str(state),
            "--defer-batch",
            "1",
        ]
    )

    assert status == 0
    ledger = load_ledger(state)
    assert ledger["claude:a"] == LedgerEntry(harvested=4, deferred=False)
    assert ledger["claude:b"] == LedgerEntry(harvested=0, deferred=True)
    assert ledger["claude:c"] == LedgerEntry(harvested=0, deferred=True)


def test_commit_writes_committed_marker(tmp_path):
    state = tmp_path / "state"
    claude_root = tmp_path / "claude"
    _claude_session(claude_root / "proj" / "a.jsonl", ["Ask.", "More."])
    run = _extract(state, claude_root, tmp_path / "pi")
    assert not (run / "committed").exists()

    main(["commit", "--run-dir", str(run), "--state-dir", str(state)])
    assert (run / "committed").is_file()

    # A second extract the same day rewrites the pending ledger, so the
    # marker no longer describes it and must go.
    _claude_session(claude_root / "proj" / "a.jsonl", ["Ask.", "More.", "Even more."])
    assert _extract(state, claude_root, tmp_path / "pi") == run
    assert not (run / "committed").exists()


def test_extract_skips_repeated_scheduled_prompts(tmp_path):
    state = tmp_path / "state"
    claude_root = tmp_path / "claude"
    # Four sessions open with the same prompt (whitespace differs): each
    # matches three others, so all four are skipped.
    for index in range(4):
        _claude_session(
            claude_root / "proj" / f"sched{index}.jsonl",
            [
                "Run   the weekly\nreport." if index % 2 else "Run the weekly report.",
                "Go on.",
            ],
        )
    # Three sessions share a prompt: each matches only two others, so all are kept.
    for index in range(3):
        _claude_session(claude_root / "proj" / f"few{index}.jsonl", ["Fix the build.", "Thanks."])
    _claude_session(claude_root / "proj" / "unique.jsonl", ["Something new.", "Thanks."])

    run = _extract(state, claude_root, tmp_path / "pi")

    names = {p.stem for p in (run / "digests").iterdir()}
    assert names == {"claude__few0", "claude__few1", "claude__few2", "claude__unique"}


def test_adapters_drop_empty_tool_only_turns(tmp_path):
    tool_result = {"type": "tool_result", "tool_use_id": "1", "content": "output"}
    tool_use = {"type": "tool_use", "id": "1", "name": "Bash", "input": {}}
    claude_path = _write_jsonl(
        tmp_path / "c.jsonl",
        [
            {"type": "user", "cwd": "/w", "message": {"content": "Only real ask."}},
            {"type": "assistant", "cwd": "/w", "message": {"content": [tool_use]}},
            {"type": "user", "cwd": "/w", "message": {"content": [tool_result]}},
            {"type": "assistant", "cwd": "/w", "message": {"content": [tool_use]}},
            {"type": "user", "cwd": "/w", "message": {"content": [tool_result]}},
            {
                "type": "assistant",
                "cwd": "/w",
                "message": {"content": [{"type": "text", "text": "Done."}]},
            },
        ],
    )
    pi_path = _write_jsonl(
        tmp_path / "p.jsonl",
        [
            {"type": "session", "id": "p1", "cwd": "/w"},
            {
                "type": "message",
                "message": {
                    "role": "user",
                    "content": [{"type": "text", "text": "Ask."}],
                },
            },
            {
                "type": "message",
                "message": {"role": "assistant", "content": [{"type": "toolCall"}]},
            },
            {
                "type": "message",
                "message": {"role": "user", "content": [{"type": "image"}]},
            },
        ],
    )

    claude = harvest.read_claude(claude_path)
    pi = harvest.read_pi(pi_path)

    assert [m.role for m in claude.messages] == ["user", "assistant"]
    assert [m.role for m in pi.messages] == ["user"]
    # One real user turn is not two exchanges, however many tool turns padded it.
    assert not harvest.is_harvestable(claude)
    digest = harvest.render_digest(claude, start=0)
    assert all(line not in ("USER: ", "ASSISTANT: ") for line in digest.splitlines())


def test_wrapper_and_pi_skill_bodies_are_filtered(tmp_path):
    wrappers = [
        "<local-command-stdout>ok</local-command-stdout>",
        "<local-command-stderr>err</local-command-stderr>",
        "<paseo-system>\nAgent finished.</paseo-system>",
        '<skill name="walkthrough" location="/x/SKILL.md">\nbody\n</skill>\n\nthese',
        "<command-name>/x</command-name>",
    ]
    claude = harvest.read_claude(
        _claude_session(tmp_path / "c.jsonl", ["Real ask.", *wrappers, "Real follow-up."])
    )
    pi = harvest.read_pi(_pi_session(tmp_path / "p.jsonl", "p1", ["Real ask.", *wrappers]))

    assert [m.text for m in claude.messages if m.role == "user"] == [
        "Real ask.",
        "Real follow-up.",
    ]
    assert [m.text for m in pi.messages if m.role == "user"] == ["Real ask."]


def test_pi_skill_invocation_counts_as_self_tagged(tmp_path):
    later = ["Then this.", "And this."]
    by_command = harvest.read_pi(
        _pi_session(tmp_path / "a.jsonl", "a", ["/skill:harvest-knowledge run", *later])
    )
    by_body = harvest.read_pi(
        _pi_session(
            tmp_path / "b.jsonl",
            "b",
            [
                '<skill name="harvest-knowledge" location="/x/SKILL.md">\nbody\n</skill>',
                *later,
            ],
        )
    )
    other_skill = harvest.read_pi(
        _pi_session(
            tmp_path / "c.jsonl",
            "c",
            [
                '<skill name="walkthrough" location="/x/SKILL.md">\nbody\n</skill>',
                *later,
            ],
        )
    )

    assert not harvest.is_harvestable(by_command)
    assert not harvest.is_harvestable(by_body)
    assert harvest.is_harvestable(other_skill)


def test_batch_uses_plan_order_from_extract(tmp_path):
    state = tmp_path / "state"
    claude_root = tmp_path / "claude"
    old = _claude_session(claude_root / "proj" / "old.jsonl", ["Old ask.", "More."])
    new = _claude_session(claude_root / "proj" / "new.jsonl", ["New ask.", "More."])
    os.utime(old, (1_000, 1_000))
    os.utime(new, (2_000, 2_000))
    # A deferred session is read first, even though its transcript is newest.
    commit_ledger(state, {}, deferred={"claude:new"})
    run = _extract(state, claude_root, tmp_path / "pi")
    # Pin digest mtimes to transcript age, so mtime order alone would batch "old" first.
    os.utime(run / "digests" / "claude__new.md", (2_000, 2_000))
    os.utime(run / "digests" / "claude__old.md", (1_000, 1_000))

    # Each digest exceeds `target`, so each needs its own batch, and `cap=1` keeps one.
    summary = harvest.batch(run, target=1, cap=1, solo=0)

    assert summary["overflow_keys"] == ["claude:old"]
    assert (run / "batch0.txt").read_text().strip().endswith("claude__new.md")
