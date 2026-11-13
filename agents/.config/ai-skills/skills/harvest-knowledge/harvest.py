#!/usr/bin/env python3
"""Turn agent session transcripts into knowledge digests.

Reads Claude Code and pi session JSONL files, filters out harness noise and
scratch sessions, and renders the remaining turns as a compact text digest.
"""

# A harness runs this script with a bare `python3`, not through this repo's
# environment, so it stays clear of syntax newer than Python 3.10 has (no
# PEP 695 generics).
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

_COMMAND_WRAPPER_PREFIXES = ("<command", "<system")
_SKILL_BODY_MARKER = "Base directory for this skill"
_SELF_TAG = "[harvest-knowledge]"
_MIN_USER_MESSAGES = 2


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

    Both roots lay sessions out as `<root>/<project-dir>/<file>.jsonl`, so
    this globs one level deep under each. A root that doesn't exist is
    skipped rather than raising, since a machine may have only one agent
    installed.
    """
    paths: list[Path] = []
    for root in (claude_root, pi_root):
        if not root.is_dir():
            continue
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
