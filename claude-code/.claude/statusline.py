#!/usr/bin/env python3
"""Claude Code status line: the built-in segments plus a context-usage bar.

Claude Code runs this on every render, passing a JSON status object on stdin and
displaying stdout as the status line. Configuring `statusLine` replaces the
built-in line entirely, so the directory/git/model/style segments here exist to
preserve what the default showed.

Every segment is optional by construction: a missing stdin field, an unreadable
transcript, or an absent git binary drops that one segment rather than failing
the line. A status line that raises is a status line that shows a traceback on
every keystroke.
"""

from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys

# Claude Code's standard window. `exceeds_200k_tokens` in the status object marks
# a session on the 1M-token beta; CLAUDE_STATUSLINE_CONTEXT_WINDOW overrides both.
DEFAULT_CONTEXT_WINDOW = 200_000
LARGE_CONTEXT_WINDOW = 1_000_000

# Percentages at which the bar changes colour. WARN and DANGER are the boundaries
# the colours describe, and DANGER is also where the skull appears.
WARN_PERCENT = 50
DANGER_PERCENT = 75

BAR_WIDTH = 10
BAR_FULL = "▓"
BAR_EMPTY = "░"
SKULL = "💀"

RESET = "\033[0m"
DIM = "\033[2m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"
CYAN = "\033[36m"

SEPARATOR = f"{DIM}  {RESET}"

# Only bytes near the end of the transcript are scanned for the newest usage
# record; see read_context_tokens for the full-file fallback.
TRANSCRIPT_TAIL_BYTES = 1_000_000


def git_segment(cwd: str) -> str | None:
    """Return "branch" or "branch*" (dirty), or None outside a work tree.

    Runs two short git commands; any failure -- no git, not a repo, a timeout on
    a slow network mount -- yields None so the caller drops the segment.
    """

    def git(*args: str) -> str | None:
        try:
            result = subprocess.run(
                ["git", *args],
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=1,
                check=False,
            )
        except (OSError, subprocess.SubprocessError):
            return None
        if result.returncode != 0:
            return None
        return result.stdout.strip()

    branch = git("rev-parse", "--abbrev-ref", "HEAD")
    if not branch:
        return None
    if branch == "HEAD":
        # Detached: a short SHA is more useful than the literal word "HEAD".
        branch = git("rev-parse", "--short", "HEAD") or "detached"

    # --porcelain prints one line per change, so any output at all means dirty.
    dirty = git("status", "--porcelain")
    return f"{branch}*" if dirty else branch


def iter_transcript_lines_reversed(path: str):
    """Yield transcript lines newest-first, reading only the tail if it suffices.

    Transcripts grow to many megabytes and this runs on every render, so the tail
    is tried first. The caller re-invokes with tail_only=False when the tail held
    no usable record.
    """
    with open(path, "rb") as handle:
        handle.seek(0, os.SEEK_END)
        size = handle.tell()
        start = max(0, size - TRANSCRIPT_TAIL_BYTES)
        handle.seek(start)
        data = handle.read()

    lines = data.split(b"\n")
    if start > 0 and lines:
        # The first line is almost certainly a fragment of a record that began
        # before the seek point; dropping it is cheaper than backing up.
        lines = lines[1:]
    return reversed(lines), start > 0


def usage_from_line(raw: bytes) -> int | None:
    """Total context tokens from one transcript line, or None if it has none.

    The three cache/input counts sum to exactly what the model was sent on that
    turn, which is the number the bar reports. Sidechain (subagent) turns are
    skipped: their context is not this session's.
    """
    if b'"usage"' not in raw:
        return None
    try:
        record = json.loads(raw)
    except (ValueError, UnicodeDecodeError):
        return None
    if not isinstance(record, dict):
        return None
    if record.get("type") != "assistant" or record.get("isSidechain"):
        return None
    message = record.get("message")
    if not isinstance(message, dict):
        return None
    usage = message.get("usage")
    if not isinstance(usage, dict):
        return None

    total = 0
    for key in ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens"):
        value = usage.get(key)
        if isinstance(value, int):
            total += value
    return total or None


def read_context_tokens(path: str | None) -> int | None:
    """Context tokens on the most recent main-chain assistant turn, or None."""
    if not path:
        return None
    try:
        lines, was_truncated = iter_transcript_lines_reversed(path)
    except OSError:
        return None

    for raw in lines:
        tokens = usage_from_line(raw)
        if tokens is not None:
            return tokens

    if not was_truncated:
        return None

    # A tail full of large tool results can contain no assistant turn at all.
    try:
        with open(path, "rb") as handle:
            for raw in reversed(handle.read().split(b"\n")):
                tokens = usage_from_line(raw)
                if tokens is not None:
                    return tokens
    except OSError:
        return None
    return None


def context_segment(tokens: int, window: int) -> str:
    percent = min(100, round(tokens / window * 100))
    if percent >= DANGER_PERCENT:
        colour = RED
    elif percent >= WARN_PERCENT:
        colour = YELLOW
    else:
        colour = GREEN

    filled = min(BAR_WIDTH, round(percent / 100 * BAR_WIDTH))
    bar = BAR_FULL * filled + BAR_EMPTY * (BAR_WIDTH - filled)
    segment = f"{colour}{bar} {percent}%{RESET}"
    if percent >= DANGER_PERCENT:
        segment += f" {SKULL}"
    return segment


def context_window(status: dict) -> int:
    override = os.environ.get("CLAUDE_STATUSLINE_CONTEXT_WINDOW")
    if override:
        try:
            parsed = int(override)
        except ValueError:
            parsed = 0
        if parsed > 0:
            return parsed
    if status.get("exceeds_200k_tokens"):
        return LARGE_CONTEXT_WINDOW
    return DEFAULT_CONTEXT_WINDOW


def directory_segment(cwd: str) -> str:
    path = pathlib.Path(cwd)
    try:
        return f"~/{path.relative_to(pathlib.Path.home())}"
    except ValueError:
        return str(path)


def build_line(status: dict) -> str:
    workspace = status.get("workspace") or {}
    cwd = workspace.get("current_dir") or status.get("cwd") or os.getcwd()

    segments = [f"{CYAN}{directory_segment(cwd)}{RESET}"]

    branch = git_segment(cwd)
    if branch:
        segments.append(f"{DIM}{branch}{RESET}")

    model = (status.get("model") or {}).get("display_name")
    if model:
        segments.append(model)

    style = (status.get("output_style") or {}).get("name")
    if style and style.lower() != "default":
        segments.append(f"{DIM}{style}{RESET}")

    tokens = read_context_tokens(status.get("transcript_path"))
    if tokens is not None:
        segments.append(context_segment(tokens, context_window(status)))

    return SEPARATOR.join(segments)


def main() -> int:
    try:
        status = json.load(sys.stdin)
    except (ValueError, OSError):
        status = {}
    if not isinstance(status, dict):
        status = {}
    try:
        print(build_line(status))
    except Exception:  # noqa: BLE001 - a status line must never show a traceback
        print(directory_segment(os.getcwd()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
