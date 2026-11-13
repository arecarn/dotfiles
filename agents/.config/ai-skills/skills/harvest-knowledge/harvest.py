#!/usr/bin/env python3
"""Turn agent session transcripts into knowledge digests.

Reads Claude Code and pi session JSONL files, filters out harness noise and
scratch sessions, and renders the remaining turns as a compact text digest.
"""

# A harness runs this script with a bare `python3`, not through this repo's
# environment, so it stays clear of syntax newer than Python 3.10 has (no
# PEP 695 generics).
from __future__ import annotations

import argparse
import datetime
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path

_COMMAND_WRAPPER_PREFIXES = ("<command", "<system")
_SKILL_BODY_MARKER = "Base directory for this skill"
_SELF_TAG = "[harvest-knowledge]"
_MIN_USER_MESSAGES = 2

_DEFAULT_CLAUDE_ROOT = Path.home() / ".claude" / "projects"
_DEFAULT_PI_ROOT = Path.home() / ".pi" / "agent" / "sessions"
_DEFAULT_STATE_DIR = Path.home() / ".local" / "state" / "knowledge-harvest"


@dataclass(frozen=True)
class Message:
    """One chat turn kept from a session transcript."""

    role: str  # "user" or "assistant"
    text: str


@dataclass(frozen=True)
class Session:
    """A session transcript reduced to the turns worth harvesting."""

    id: str
    source: str  # "claude" or "pi"
    path: Path
    cwd: str
    messages: tuple[Message, ...]


def _text_from_content(content: object) -> str:
    """Join the text parts of a message's `content`, dropping tool_use/tool_result parts.

    `content` is either a plain string or a list of typed parts (Claude's
    and pi's content-part shapes agree on `{"type": "text", "text": ...}`);
    anything else (tool_use, tool_result, images) is skipped.
    """
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = [
            item.get("text", "")
            for item in content
            if isinstance(item, dict) and item.get("type") == "text"
        ]
        return "\n".join(parts)
    return ""


def _is_noise_user_text(text: str) -> bool:
    """True for a user message that is a harness-injected wrapper rather than something a human typed.

    Matches the filters from the earlier one-off harvest: slash-command and
    system-reminder wrappers, and the skill-body banner a skill invocation
    injects as a synthetic user turn.
    """
    head = text[:200]
    return head.startswith(_COMMAND_WRAPPER_PREFIXES) or _SKILL_BODY_MARKER in head


def read_claude(path: Path) -> Session | None:
    """Parse a Claude Code session JSONL file into a Session.

    Drops records with `isMeta` or `isSidechain` true, and drops user
    messages that are harness wrappers rather than human-typed text (see
    `_is_noise_user_text`). Tolerates a truncated last line by skipping any
    line that fails to parse. Returns None if no line carries a `cwd`, which
    means there was nothing usable to build a session from.
    """
    cwd: str | None = None
    messages: list[Message] = []
    with path.open(encoding="utf-8") as fh:
        for raw_line in fh:
            line = raw_line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            role = record.get("type")
            if role not in ("user", "assistant"):
                continue
            if record.get("isMeta") or record.get("isSidechain"):
                continue
            if cwd is None and record.get("cwd"):
                cwd = record["cwd"]
            message = record.get("message") or {}
            text = _text_from_content(message.get("content"))
            if role == "user" and _is_noise_user_text(text):
                continue
            messages.append(Message(role=role, text=text))
    if cwd is None:
        return None
    return Session(id=path.stem, source="claude", path=path, cwd=cwd, messages=tuple(messages))


def read_pi(path: Path) -> Session | None:
    """Parse a pi agent session JSONL file into a Session.

    The first line is a `{"type": "session", "id": ..., "cwd": ...}` header;
    later lines are `{"type": "message", ...}` records, kept only when the
    message role is "user" or "assistant" (drops "toolResult" and "system").
    Returns None if the header line is missing.
    """
    session_id: str | None = None
    cwd: str | None = None
    messages: list[Message] = []
    with path.open(encoding="utf-8") as fh:
        for raw_line in fh:
            line = raw_line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            rtype = record.get("type")
            if rtype == "session":
                session_id = record.get("id")
                cwd = record.get("cwd")
                continue
            if rtype != "message":
                continue
            message = record.get("message") or {}
            role = message.get("role")
            if role not in ("user", "assistant"):
                continue
            text = _text_from_content(message.get("content"))
            messages.append(Message(role=role, text=text))
    if session_id is None or cwd is None:
        return None
    return Session(id=session_id, source="pi", path=path, cwd=cwd, messages=tuple(messages))


def discover(claude_root: Path, pi_root: Path) -> list[Path]:
    """List every session JSONL file under the Claude and pi session roots.

    Globs recursively under each root, so it finds both the real layout
    (`<root>/<project-dir>/<file>.jsonl`) and a flat root used directly in
    tests. A root that doesn't exist is skipped rather than raising, since
    a machine may have only one agent installed.
    """
    paths: list[Path] = []
    for root in (claude_root, pi_root):
        if not root.is_dir():
            continue
        paths.extend(sorted(root.glob("**/*.jsonl")))
    return paths


def is_harvestable(session: Session) -> bool:
    """Whether a session is worth digesting.

    False for a scratch session (cwd under `/tmp/`), a session with fewer
    than two human turns, or a session already tagged as this tool's own
    output (first user message starts with `[harvest-knowledge]`).
    """
    if session.cwd.startswith("/tmp/"):
        return False
    user_messages = [m for m in session.messages if m.role == "user"]
    if len(user_messages) < _MIN_USER_MESSAGES:
        return False
    if user_messages[0].text.strip().startswith(_SELF_TAG):
        return False
    return True


def render_digest(session: Session, start: int, cap: int = 1100) -> str:
    """Render `session.messages[start:]` as a text digest.

    The first line names the session so a digest file is self-describing
    without its name; each following line is one message, labelled
    "USER: "/"ASSISTANT: ", with embedded newlines flattened to spaces and
    the text cut to `cap` characters.
    """
    lines = [f"# session {session.id} source={session.source} cwd={session.cwd}"]
    for message in session.messages[start:]:
        label = "USER: " if message.role == "user" else "ASSISTANT: "
        flat = message.text.replace("\n", " ").replace("\r", " ")
        lines.append(label + flat[:cap])
    return "\n".join(lines)


@dataclass
class LedgerEntry:
    """How much of one session has already been harvested.

    `harvested` is a count of `session.messages` already turned into a
    digest; `deferred` marks a session a prior commit explicitly held back
    (see `commit_ledger`), which `plan_extract` reads to prioritize it.
    """

    harvested: int
    deferred: bool = False


def _ledger_key(source: str, session_id: str) -> str:
    return f"{source}:{session_id}"


def _ledger_to_json(ledger: dict[str, LedgerEntry]) -> dict:
    return {key: {"harvested": entry.harvested, "deferred": entry.deferred} for key, entry in ledger.items()}


def _ledger_from_json(data: dict) -> dict[str, LedgerEntry]:
    return {
        key: LedgerEntry(harvested=value["harvested"], deferred=value.get("deferred", False))
        for key, value in data.items()
    }


def _write_json_atomic(path: Path, data: dict) -> None:
    """Write `data` as JSON to `path`, replacing it atomically.

    Writes to a sibling `.tmp` file first and `os.replace`s it over the
    target, so a reader never observes a partially-written file and a
    crash mid-write leaves the previous contents intact.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(path.name + ".tmp")
    with tmp_path.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, sort_keys=True)
    os.replace(tmp_path, path)


def load_ledger(state: Path) -> dict[str, LedgerEntry]:
    """Load `state/ledger.json` into `{key: LedgerEntry}`.

    The key is `f"{session.source}:{session.id}"`. Returns `{}` when the
    file is missing (first run, or a state dir not yet initialized).
    """
    path = state / "ledger.json"
    if not path.is_file():
        return {}
    with path.open(encoding="utf-8") as fh:
        data = json.load(fh)
    return _ledger_from_json(data)


def plan_extract(
    sessions: list[Session], ledger: dict[str, LedgerEntry]
) -> list[tuple[Session, int]]:
    """Decide, per session, where a digest should resume and in what order.

    For each session, compares `ledger[f"{source}:{id}"].harvested` (0 if
    absent) against `len(session.messages)`: a session with nothing new
    past that offset is omitted, and a session whose message count is now
    below its recorded offset (history was replaced, not just appended) is
    restarted from 0 rather than skipped. The result orders deferred
    sessions first, then the rest oldest-by-mtime first within each group,
    using `session.path.stat().st_mtime`.
    """
    candidates = []
    for session in sessions:
        entry = ledger.get(_ledger_key(session.source, session.id))
        harvested = entry.harvested if entry is not None else 0
        deferred = entry.deferred if entry is not None else False
        start = 0 if harvested > len(session.messages) else harvested
        if start >= len(session.messages):
            continue
        candidates.append((session, start, deferred))
    candidates.sort(key=lambda item: (not item[2], item[0].path.stat().st_mtime))
    return [(session, start) for session, start, _deferred in candidates]


def write_digests(plan: list[tuple[Session, int]], run_dir: Path) -> list[Path]:
    """Render each planned session's digest into `run_dir/digests/`.

    Each file is named `<source>__<id>.md` (double underscore), so the
    ledger key `source:id` is recoverable from the filename alone (used by
    Task 3). Clears and recreates `run_dir/digests/` first, so re-running
    `extract` for the same run dir overwrites rather than accumulating
    stale files from a prior attempt. Returns the written paths.
    """
    digests_dir = run_dir / "digests"
    if digests_dir.exists():
        for existing in digests_dir.iterdir():
            existing.unlink()
    else:
        digests_dir.mkdir(parents=True)
    written = []
    for session, start in plan:
        text = render_digest(session, start)
        path = digests_dir / f"{session.source}__{session.id}.md"
        path.write_text(text, encoding="utf-8")
        written.append(path)
    return written


def pending_ledger(plan: list[tuple[Session, int]]) -> dict[str, LedgerEntry]:
    """Compute the ledger entries a plan would produce, without writing them.

    Each planned session's new `harvested` value is `len(session.messages)`
    (the whole session is covered by the digest just rendered for it).
    `deferred` is always False here; `commit_ledger` is what applies any
    `--deferred` override.
    """
    return {
        _ledger_key(session.source, session.id): LedgerEntry(harvested=len(session.messages))
        for session, _start in plan
    }


def commit_ledger(state: Path, updates: dict[str, LedgerEntry], deferred: set[str]) -> None:
    """Merge `updates` into `state/ledger.json` and write it atomically.

    For a key in `deferred`, the update is not applied: the entry keeps
    whatever `harvested` value it already had in the ledger (0 if it had
    none) and is marked `deferred=True`, so a deferred session's digest is
    re-offered, in full, on the next `extract`. Every other key in
    `updates` is written as given, with `deferred=False`.
    """
    existing = load_ledger(state)
    merged = dict(existing)
    for key in deferred:
        previous = existing.get(key)
        incoming = updates.get(key)
        harvested = previous.harvested if previous is not None else (incoming.harvested if incoming is not None else 0)
        merged[key] = LedgerEntry(harvested=harvested, deferred=True)
    for key, entry in updates.items():
        if key in deferred:
            continue
        merged[key] = LedgerEntry(harvested=entry.harvested, deferred=False)
    _write_json_atomic(state / "ledger.json", _ledger_to_json(merged))


def _is_under(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _collect_sessions(claude_root: Path, pi_root: Path) -> list[Session]:
    """Read every discovered session file with the reader matching its root, keeping only harvestable ones."""
    sessions = []
    for path in discover(claude_root, pi_root):
        if _is_under(path, claude_root):
            session = read_claude(path)
        elif _is_under(path, pi_root):
            session = read_pi(path)
        else:
            continue
        if session is None or not is_harvestable(session):
            continue
        sessions.append(session)
    return sessions


def extract(state_dir: Path, claude_root: Path, pi_root: Path) -> dict:
    """Plan and write one day's digests under `state_dir`.

    Reads `state_dir/ledger.json` (via `load_ledger`) to decide which
    messages are new, but this function never writes `ledger.json` itself
    -- it writes the run's digests and a `pending-ledger.json` proposal
    only. A `commit` run applies that proposal; since the proposal exists
    on disk before any ledger write, a crash between `extract` and
    `commit` is safe to retry without double-counting or losing anything.

    Writes to `state_dir/runs/<today>/digests/` and
    `state_dir/runs/<today>/pending-ledger.json`. Reuses `<today>`'s run
    dir if one already exists (a second run the same day), overwriting the
    digests. Returns `{"run_dir", "sessions", "bytes"}`.
    """
    today = datetime.date.today().isoformat()
    run_dir = state_dir / "runs" / today
    run_dir.mkdir(parents=True, exist_ok=True)

    ledger = load_ledger(state_dir)
    sessions = _collect_sessions(claude_root, pi_root)
    plan = plan_extract(sessions, ledger)

    written = write_digests(plan, run_dir)
    total_bytes = sum(path.stat().st_size for path in written)
    _write_json_atomic(run_dir / "pending-ledger.json", _ledger_to_json(pending_ledger(plan)))

    return {"run_dir": str(run_dir), "sessions": len(plan), "bytes": total_bytes}


def commit(run_dir: Path, state_dir: Path, deferred_keys: set[str]) -> None:
    """Apply a run's `pending-ledger.json` to `state_dir/ledger.json`.

    Requires `run_dir/pending-ledger.json` to exist (written by a prior
    `extract`). Keys in `deferred_keys` keep their previous `harvested`
    value and are marked `deferred=True`; see `commit_ledger`.
    """
    pending_path = run_dir / "pending-ledger.json"
    with pending_path.open(encoding="utf-8") as fh:
        data = json.load(fh)
    commit_ledger(state_dir, _ledger_from_json(data), deferred_keys)


def main(argv: list[str] | None = None) -> int:
    """CLI entry point for the `extract` and `commit` subcommands."""
    parser = argparse.ArgumentParser(prog="harvest.py")
    subparsers = parser.add_subparsers(dest="command", required=True)

    extract_parser = subparsers.add_parser("extract", help="Render new session turns into digests")
    extract_parser.add_argument("--state-dir", type=Path, default=_DEFAULT_STATE_DIR)
    extract_parser.add_argument("--claude-root", type=Path, default=_DEFAULT_CLAUDE_ROOT)
    extract_parser.add_argument("--pi-root", type=Path, default=_DEFAULT_PI_ROOT)

    commit_parser = subparsers.add_parser("commit", help="Apply a run's pending ledger")
    commit_parser.add_argument("--run-dir", type=Path, required=True)
    commit_parser.add_argument("--state-dir", type=Path, default=_DEFAULT_STATE_DIR)
    commit_parser.add_argument("--deferred", action="append", default=[], metavar="KEY")

    args = parser.parse_args(argv)

    if args.command == "extract":
        summary = extract(args.state_dir, args.claude_root, args.pi_root)
        print(json.dumps(summary))
    elif args.command == "commit":
        commit(args.run_dir, args.state_dir, set(args.deferred))

    return 0


if __name__ == "__main__":
    sys.exit(main())
