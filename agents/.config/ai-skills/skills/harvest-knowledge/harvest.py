#!/usr/bin/env python3
"""Turn agent session transcripts into knowledge digests.

Reads Claude Code and pi session JSONL files, filters out harness noise and
scratch sessions, and renders the remaining turns as a compact text digest.
"""

# A harness runs this script with a bare `python3`, not through this repo's
# environment, so it stays clear of syntax newer than Python 3.10 has (no
# PEP 695 generics). It ships as one file beside SKILL.md, which imports it
# by path, so it is not split to stay under pylint's module-length limit.
# pylint: disable=too-many-lines
from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

_COMMAND_WRAPPER_PREFIXES = ("<command", "<system")
_SKILL_BODY_MARKER = "Base directory for this skill"
_SELF_TAG = "[harvest-knowledge]"
_MIN_USER_MESSAGES = 2

_DEFAULT_CLAUDE_ROOT = Path.home() / ".claude" / "projects"
_DEFAULT_PI_ROOT = Path.home() / ".pi" / "agent" / "sessions"
_DEFAULT_STATE_DIR = Path.home() / ".local" / "state" / "knowledge-harvest"
_DEFAULT_KNOWLEDGE_DIR = Path.home() / ".config" / "ai-knowledge"
_DEFAULT_PRIVATE_ROOT = Path.home() / "dotfiles_local"


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


@dataclass(frozen=True)
class Bundle:
    """A knowledge bundle discovered under a knowledge directory.

    `root` is the bundle's directory as found (a symlink target is not
    resolved); `private` is True when `root.resolve()` lies under the
    private-knowledge root, which is how a bundle stowed from
    `dotfiles_local` is told apart from one that ships in the public repo.
    """

    id: str
    root: Path
    private: bool


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
    """True for a user message that is a harness-injected wrapper, not something a human typed.

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
    """List every top-level session JSONL file under the Claude and pi session roots.

    Globs depth 0 (a flat root, used directly in tests) and depth 1 (the
    real layout, `<root>/<project-dir>/<file>.jsonl`) only -- never deeper.
    Both tools nest subagent/fork transcripts several levels under a
    session file (pi: `<dir>/<session>/<subagent-id>/run-0/session.jsonl`,
    `<dir>/<session>/forks/<id>.jsonl`; Claude:
    `<project>/<session-id>/subagents/**/*.jsonl`), and those still parse
    as standalone sessions, so a recursive glob would harvest them as
    top-level sessions. A root that doesn't exist is skipped rather than
    raising, since a machine may have only one agent installed.
    """
    paths: list[Path] = []
    for root in (claude_root, pi_root):
        if not root.is_dir():
            continue
        paths.extend(sorted(root.glob("*.jsonl")))
        paths.extend(sorted(root.glob("*/*.jsonl")))
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
    return {
        key: {"harvested": entry.harvested, "deferred": entry.deferred}
        for key, entry in ledger.items()
    }


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
        harvested = previous.harvested if previous is not None else 0
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
    """Read every discovered file with the reader matching its root, keeping only harvestable
    sessions."""
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
    digests and removing that dir's `committed` marker, since the marker
    described the pending ledger this call replaces. Returns
    `{"run_dir", "sessions", "bytes"}`.
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
    # The marker described the pending ledger just replaced.
    (run_dir / "committed").unlink(missing_ok=True)

    return {"run_dir": str(run_dir), "sessions": len(plan), "bytes": total_bytes}


class CommitError(Exception):
    """A `commit` refused to touch the ledger; the message says why."""


def _keys_from_list_file(path: Path) -> set[str]:
    """Read a `batch<N>.txt` or `overflow.txt` file into the ledger keys of the digests it lists."""
    lines = path.read_text(encoding="utf-8").splitlines()
    return {_key_from_digest_path(Path(line.strip())) for line in lines if line.strip()}


def commit(
    run_dir: Path, state_dir: Path, deferred_keys: set[str], defer_batches: list[int] | None = None
) -> None:
    """Apply a run's `pending-ledger.json` to `state_dir/ledger.json`, then mark the run committed.

    The deferred set is the union of `deferred_keys`, every key listed in
    `run_dir/overflow.txt` (when `batch` wrote one), and every key listed in
    `run_dir/batch<N>.txt` for each N in `defer_batches`. Deferred keys keep
    their previous `harvested` value and are marked `deferred=True`; see
    `commit_ledger`. On success writes `run_dir/committed` (a timestamp),
    which tells a later run that this run's ledger already landed.

    Requires `run_dir/pending-ledger.json` (written by `extract`). Raises
    `CommitError`, before writing anything, when a deferred key is not in the
    pending ledger (a mistyped key would otherwise add a junk entry) or a
    named batch file does not exist.
    """
    pending_path = run_dir / "pending-ledger.json"
    with pending_path.open(encoding="utf-8") as fh:
        pending = _ledger_from_json(json.load(fh))

    deferred = set(deferred_keys)
    overflow_path = run_dir / "overflow.txt"
    if overflow_path.is_file():
        deferred |= _keys_from_list_file(overflow_path)
    for number in defer_batches or []:
        batch_path = run_dir / f"batch{number}.txt"
        if not batch_path.is_file():
            raise CommitError(f"no such batch file: {batch_path}")
        deferred |= _keys_from_list_file(batch_path)

    unknown = sorted(deferred - set(pending))
    if unknown:
        raise CommitError(
            f"deferred keys not in {pending_path}: {', '.join(unknown)}; ledger left unchanged"
        )

    commit_ledger(state_dir, pending, deferred)
    stamp = datetime.datetime.now().isoformat(timespec="seconds")
    (run_dir / "committed").write_text(stamp + "\n", encoding="utf-8")


def discover_bundles(knowledge_dir: Path, private_root: Path) -> list[Bundle]:
    """List every knowledge bundle directly under `knowledge_dir`.

    A bundle is a directory or symlink (`config.yaml`'s own doc: a bundle
    "is" whatever sits beside it with an `index.md`) whose `index.md` has an
    `okf_version` key in its frontmatter. Non-bundle entries (`config.yaml`,
    a bundle missing `okf_version`) are skipped rather than raising, since a
    knowledge directory also holds files that are not bundles.
    """
    bundles = []
    if not knowledge_dir.is_dir():
        return bundles
    private_resolved = private_root.resolve()
    for entry in sorted(knowledge_dir.iterdir()):
        index = entry / "index.md"
        if not index.is_file():
            continue
        frontmatter = _read_frontmatter_lines(index)
        if not any(line.strip().startswith("okf_version:") for line in frontmatter):
            continue
        private = _is_under(entry.resolve(), private_resolved)
        bundles.append(Bundle(id=entry.name, root=entry, private=private))
    return bundles


def _read_frontmatter_lines(path: Path) -> list[str]:
    """Return the lines between a markdown file's `---` delimiters, or `[]` if it has none."""
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        return []
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            return lines[1:index]
    return []


def _unquote_scalar(value: str) -> str:
    """Strip one layer of matching `"`/`'` quoting from a YAML scalar.

    Returns `value` unchanged when it is not quoted.
    """
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    return value


def entry_sources(md: Path) -> tuple[str | None, list[str]]:
    """Read a knowledge entry's `verified` date and `sources` list from its frontmatter.

    Handles the two YAML forms the bundles use: a scalar key (`verified:
    "2026-10-06"`, quoted with `"` or `'`, or bare) and a block list whose
    items are quoted strings (`  - "item"`). Returns `(None, [])` when the
    file has no frontmatter or no `verified` key -- callers use that to
    skip an entry with nothing to check staleness against.
    """
    verified: str | None = None
    sources: list[str] = []
    in_sources = False
    for line in _read_frontmatter_lines(md):
        stripped = line.strip()
        if not stripped:
            continue
        if line.startswith((" ", "\t")) and stripped.startswith("-"):
            if in_sources:
                sources.append(_unquote_scalar(stripped[1:]))
            continue
        in_sources = False
        key, _, rest = stripped.partition(":")
        key = key.strip()
        if key == "verified":
            verified = _unquote_scalar(rest)
        elif key == "sources":
            in_sources = True
    return verified, sources


def _yaml_list_items(lines: list[str], list_key: str) -> list[dict[str, str]]:
    """Parse a top-level YAML `list_key:` block of `- key: value` mapping items.

    Each item starts with a `-`-prefixed line (`- name: ...`) and continues
    with more deeply indented `key: value` lines until the next `-` at the
    same indent or a line outdented back out of the block. Only scalar
    `key: value` pairs are kept; a nested block (for example `scopes:`'s own
    list) is skipped, since `repositories.yaml` entries only need `name`
    and `local` here.
    """
    items: list[dict[str, str]] = []
    in_list = False
    list_indent = 0
    current: dict[str, str] | None = None
    item_indent = 0
    for line in lines:
        if not line.strip() or line.strip().startswith("#"):
            continue
        indent = len(line) - len(line.lstrip(" "))
        stripped = line.strip()
        if not in_list:
            if stripped == f"{list_key}:":
                in_list = True
                list_indent = indent
            continue
        if indent < list_indent:
            break
        if indent == list_indent and stripped.startswith("-"):
            if current is not None:
                items.append(current)
            current = {}
            item_indent = indent
            stripped = stripped[1:].strip()
            if not stripped:
                continue
        elif current is None or indent <= item_indent:
            continue
        key, sep, rest = stripped.partition(":")
        if sep and current is not None:
            current[key.strip()] = _unquote_scalar(rest)
    if current is not None:
        items.append(current)
    return items


def repo_paths(bundles: list[Bundle], workspace_roots: list[Path]) -> dict[str, Path]:
    """Map repository names to local checkouts, from every bundle's `repositories.yaml`.

    Each repository is keyed by both its `name:` value and the basename of
    its `path:` value (source text names repositories by the GitLab path's
    last segment, for example `group/RepoA`'s `RepoA`, not by `name:`). A
    repository's `local:` path is resolved against `workspace_roots` in
    order; the first root under which `root / local` exists and contains
    `.git` wins, and a repository that resolves under no root is omitted.
    """
    paths: dict[str, Path] = {}
    for bundle in bundles:
        yaml_path = bundle.root / "repositories.yaml"
        if not yaml_path.is_file():
            continue
        lines = yaml_path.read_text(encoding="utf-8").splitlines()
        for item in _yaml_list_items(lines, "repositories"):
            name = item.get("name")
            local = item.get("local")
            if not name or not local:
                continue
            for root in workspace_roots:
                candidate = root / local
                if (candidate / ".git").exists():
                    paths[name] = candidate
                    paths[PurePosixPath(item.get("path", "")).name or name] = candidate
                    break
    return paths


def _ordered_repo_names(repo_paths_map: dict[str, Path]) -> list[str]:
    """Order repository names longest-first, so a short name can't match inside a longer one."""
    return sorted(repo_paths_map, key=len, reverse=True)


_TOKEN_RE = re.compile(r"[A-Za-z0-9_./-]+")


def resolve_source(text: str, repo_paths_map: dict[str, Path]) -> tuple[Path, list[str]] | None:
    """Find a known repository and the files it names in one `sources` entry's text.

    Matches a repository name as a whole word (so `Repo` does not match
    inside `RepoAB`), trying longer names first. Once a repository is
    found, collects the path-like tokens in the text (`a/b.ext`, or a bare
    `name.ext`) that actually exist in its checkout: a bare name is looked
    up with `git ls-files -- '**/name.ext'` so it matches at any depth, and
    a slash-containing token is checked as a literal path. Returns `None`
    when the text names no known repository, or a known repository with no
    file that resolves (for example a DNG module citation).
    """
    for name in _ordered_repo_names(repo_paths_map):
        if re.search(rf"\b{re.escape(name)}\b", text):
            repo_root = repo_paths_map[name]
            break
    else:
        return None

    files: list[str] = []
    for token in _TOKEN_RE.findall(text):
        if "." not in token.rsplit("/", 1)[-1]:
            continue  # not a file-shaped token (e.g. a commit SHA or branch name)
        if "/" in token:
            if (repo_root / token).is_file():
                files.append(token)
            continue
        result = subprocess.run(
            ["git", "ls-files", "--", f"**/{token}"],
            cwd=repo_root,
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0 and result.stdout.strip():
            files.append(result.stdout.strip().splitlines()[0])
    if not files:
        return None
    return repo_root, files


def _git_default_branch_commits(
    repo_root: Path, since: str, files: list[str], fetch: bool, fetched: dict[Path, bool]
) -> list[str] | None:
    """List `origin/HEAD`'s commits touching `files` since `since`, or `None` if git failed.

    Runs `git fetch --quiet` first unless `fetch` is False, so a stale local
    `origin/HEAD` doesn't under-report. `fetched` is a cache the caller owns
    across one `stale()` run, keyed by `repo_root`: a repository already
    fetched (successfully or not) in this run is not fetched again, so a
    repository cited by many `sources` entries is fetched at most once. A
    non-zero return from either command means the source is unresolved
    rather than raising -- including a repo with no `origin/HEAD` (for
    example one with no remote), which makes `git log` fail the same way.
    """
    if fetch:
        if repo_root not in fetched:
            fetch_result = subprocess.run(
                ["git", "fetch", "--quiet"],
                cwd=repo_root,
                check=False,
                capture_output=True,
                text=True,
            )
            fetched[repo_root] = fetch_result.returncode == 0
        if not fetched[repo_root]:
            return None
    log_result = subprocess.run(
        ["git", "log", f"--since={since}", "--oneline", "origin/HEAD", "--", *files],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )
    if log_result.returncode != 0:
        return None
    return [line for line in log_result.stdout.splitlines() if line.strip()]


def _stale_lines_for_entry(
    bundle: Bundle, md: Path, paths: dict[str, Path], fetch: bool, fetched: dict[Path, bool]
) -> tuple[list[str], int]:
    """Check one knowledge entry's `sources` list, returning its stale lines and unresolved count.

    Skipped entirely (both empty) when `md` has no `verified` date. Shares
    `fetched` with every other entry in the same `stale()` run, so a
    repository already fetched is not fetched again.
    """
    verified, sources = entry_sources(md)
    if verified is None:
        return [], 0

    lines: list[str] = []
    unresolved = 0
    for source_text in sources:
        resolved = resolve_source(source_text, paths)
        if resolved is None:
            unresolved += 1
            continue
        repo_root, files = resolved
        commits = _git_default_branch_commits(repo_root, verified, files, fetch, fetched)
        if commits is None:
            unresolved += 1
        elif commits:
            entry_label = f"{bundle.id}/{md.relative_to(bundle.root)}"
            lines.append(
                f"{entry_label} — {repo_root.name}: {len(commits)} commits to "
                f"{', '.join(files)} since {verified}"
            )
    return lines, unresolved


def stale(knowledge_dir: Path, private_root: Path, workspace_roots: list[Path], fetch: bool) -> str:
    """Build the markdown `stale` report for every bundle under `knowledge_dir`.

    Scans every `*.md` under each bundle except `index.md`, skipping an
    entry with no `verified` date. For each `sources` entry that resolves
    (see `resolve_source`) to at least one commit on `origin/HEAD` since
    `verified`, adds one line to `## May be stale`. Counts, but does not
    list, every `sources` entry that does not resolve to a known
    repository and files.
    """
    bundles = discover_bundles(knowledge_dir, private_root)
    paths = repo_paths(bundles, workspace_roots)

    stale_lines: list[str] = []
    unresolved = 0
    fetched: dict[Path, bool] = {}
    for bundle in bundles:
        for md in sorted(bundle.root.rglob("*.md")):
            if md.name == "index.md":
                continue
            entry_lines, entry_unresolved = _stale_lines_for_entry(
                bundle, md, paths, fetch, fetched
            )
            stale_lines.extend(entry_lines)
            unresolved += entry_unresolved

    roots_label = ", ".join(str(root) for root in workspace_roots) or "(none)"
    lines = [f"Workspace roots: {roots_label}", "", "## May be stale"]
    lines.extend(stale_lines if stale_lines else ["(none)"])
    lines.append(f"\nUnresolved sources: {unresolved}")
    return "\n".join(lines)


def _default_workspace_roots() -> list[Path]:
    """Compute the default `--workspace-root` list.

    Either the env var, or `~/files/projects` plus its immediate subdirectories.

    `HARVEST_WORKSPACE_ROOTS` is `os.pathsep`-separated, matching how other
    PATH-like settings are read. Falling back to scanning subdirectories
    lets a repository nested one level down (for example
    `~/files/projects/team/project`) resolve without the caller having to
    name every project folder.
    """
    env_value = os.environ.get("HARVEST_WORKSPACE_ROOTS")
    if env_value:
        return [Path(p) for p in env_value.split(os.pathsep) if p]
    base = Path.home() / "files" / "projects"
    roots = [base]
    if base.is_dir():
        roots.extend(sorted(p for p in base.iterdir() if p.is_dir()))
    return roots


def _pack_largest_first(digests: list[Path], target: int) -> list[list[Path]]:
    """Bin-pack `digests` into bins of about `target` size, largest digest first.

    A digest larger than `target` is never combined with another and gets a
    bin to itself. The rest are sorted largest-first and first-fit into the
    first bin with enough remaining capacity, opening a new bin otherwise.
    Bin count is monotonic non-decreasing as digests are added, which is what
    lets `make_batches` grow its included set one oldest digest at a time and
    stop as soon as the cap is exceeded.
    """
    oversized = [d for d in digests if d.stat().st_size > target]
    normal = sorted(
        (d for d in digests if d.stat().st_size <= target),
        key=lambda d: d.stat().st_size,
        reverse=True,
    )

    bins = [[d] for d in oversized]
    remaining_capacity: list[int] = []
    for digest in normal:
        size = digest.stat().st_size
        for index, capacity in enumerate(remaining_capacity):
            if capacity >= size:
                bins[len(oversized) + index].append(digest)
                remaining_capacity[index] -= size
                break
        else:
            bins.append([digest])
            remaining_capacity.append(target - size)
    return bins


def make_batches(
    digests: list[Path], target: int = 350_000, cap: int = 8, solo: int = 300_000
) -> tuple[list[list[Path]], list[Path]]:
    """Group digest files into batches a reader subagent can consume, with overflow for the rest.

    Returns `(batches, overflow)`. When the digests' total size is at most
    `solo`, everything goes in a single batch and overflow is empty.
    Otherwise, taking digests oldest-mtime-first, grows the included set one
    digest at a time, packing it largest-first (see `_pack_largest_first`)
    into bins of about `target` size, and stops at the first digest that
    would push the bin count past `cap`; a digest larger than `target` always
    takes a whole bin on its own. Every digest not included is overflow,
    ordered newest-mtime-first, so that the oldest unread digests are the
    ones batched now.
    """
    if not digests:
        return [], []
    total = sum(d.stat().st_size for d in digests)
    if total <= solo:
        return [list(digests)], []

    by_age = sorted(digests, key=lambda d: d.stat().st_mtime)
    included: list[Path] = []
    for digest in by_age:
        candidate = included + [digest]
        if len(_pack_largest_first(candidate, target)) <= cap:
            included = candidate
        else:
            break

    overflow = sorted(set(by_age) - set(included), key=lambda d: d.stat().st_mtime, reverse=True)
    batches = _pack_largest_first(included, target)
    return batches, overflow


def _key_from_digest_path(path: Path) -> str:
    """Recover a digest's ledger key (`source:id`) from its `<source>__<id>.md` filename.

    Splits on the first `__` only, since an id may itself contain underscores.
    """
    source, _, rest = path.stem.partition("__")
    return f"{source}:{rest}"


def batch(run_dir: Path, target: int = 350_000, cap: int = 8, solo: int = 300_000) -> dict:
    """Split `run_dir/digests/` into reader-sized batches and write them under `run_dir`.

    Writes `run_dir/batch<N>.txt` (N from 0, one absolute digest path per
    line) for each batch from `make_batches`, and `run_dir/overflow.txt`
    (one absolute path per line, empty when there's no overflow). Removes
    any stale `batch*.txt` left from an earlier same-day run first, since a
    smaller batch count here would otherwise leave old files behind. Returns
    `{"batches", "overflow_keys"}`; `commit` reads `overflow.txt` itself,
    so the keys are for reporting only.
    """
    digests = sorted((run_dir / "digests").glob("*.md"))
    for stale_batch in run_dir.glob("batch*.txt"):
        stale_batch.unlink()

    batches, overflow = make_batches(digests, target=target, cap=cap, solo=solo)

    for index, group in enumerate(batches):
        text = "".join(f"{path.resolve()}\n" for path in group)
        (run_dir / f"batch{index}.txt").write_text(text, encoding="utf-8")
    overflow_text = "".join(f"{path.resolve()}\n" for path in overflow)
    (run_dir / "overflow.txt").write_text(overflow_text, encoding="utf-8")

    return {"batches": len(batches), "overflow_keys": [_key_from_digest_path(p) for p in overflow]}


def main(argv: list[str] | None = None) -> int:
    """CLI entry point for the `extract`, `commit`, `batch`, and `stale` subcommands."""
    parser = argparse.ArgumentParser(prog="harvest.py")
    subparsers = parser.add_subparsers(dest="command", required=True)

    extract_parser = subparsers.add_parser("extract", help="Render new session turns into digests")
    extract_parser.add_argument("--state-dir", type=Path, default=_DEFAULT_STATE_DIR)
    extract_parser.add_argument("--claude-root", type=Path, default=_DEFAULT_CLAUDE_ROOT)
    extract_parser.add_argument("--pi-root", type=Path, default=_DEFAULT_PI_ROOT)

    commit_parser = subparsers.add_parser("commit", help="Apply a run's pending ledger")
    commit_parser.add_argument("--run-dir", type=Path, required=True)
    commit_parser.add_argument("--state-dir", type=Path, default=_DEFAULT_STATE_DIR)
    commit_parser.add_argument(
        "--deferred",
        action="append",
        default=[],
        metavar="KEY",
        help="defer this <source>:<id> key too (overflow.txt is always read)",
    )
    commit_parser.add_argument(
        "--defer-batch",
        action="append",
        type=int,
        default=[],
        metavar="N",
        dest="defer_batches",
        help="defer every session listed in batch<N>.txt",
    )

    batch_parser = subparsers.add_parser(
        "batch", help="Split a run's digests into reader-sized batches"
    )
    batch_parser.add_argument("--run-dir", type=Path, required=True)

    stale_parser = subparsers.add_parser(
        "stale", help="Report knowledge entries whose cited sources have changed"
    )
    stale_parser.add_argument("--knowledge-dir", type=Path, default=_DEFAULT_KNOWLEDGE_DIR)
    stale_parser.add_argument("--private-root", type=Path, default=_DEFAULT_PRIVATE_ROOT)
    stale_parser.add_argument(
        "--workspace-root", action="append", dest="workspace_roots", type=Path, default=None
    )
    stale_parser.add_argument("--no-fetch", action="store_true")

    args = parser.parse_args(argv)

    if args.command == "extract":
        summary = extract(args.state_dir, args.claude_root, args.pi_root)
        print(json.dumps(summary))
    elif args.command == "commit":
        try:
            commit(args.run_dir, args.state_dir, set(args.deferred), args.defer_batches)
        except CommitError as error:
            print(f"harvest.py commit: {error}", file=sys.stderr)
            return 1
    elif args.command == "batch":
        summary = batch(args.run_dir)
        print(json.dumps(summary))
    elif args.command == "stale":
        workspace_roots = args.workspace_roots or _default_workspace_roots()
        print(
            stale(args.knowledge_dir, args.private_root, workspace_roots, fetch=not args.no_fetch)
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
