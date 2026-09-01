#!/usr/bin/env python3
"""Claude Code status line: the built-in segments plus a context-usage bar.

Claude Code runs this on every render, passing a JSON status object on stdin and
displaying stdout as the status line. Configuring `statusLine` replaces the
built-in line entirely, so the directory/git/model/style segments here exist to
preserve what the default showed.

Every segment is optional by construction: a missing stdin field or an absent
git binary drops that one segment rather than failing the line. A status line
that raises is a status line that shows a traceback on every keystroke.
"""

from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys

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


def context_percent(status: dict) -> int | None:
    """Percent of the context window in use, or None if the harness omits it.

    Claude Code reports both the window size and the live token counts in
    `context_window`, so nothing here infers either. Do not substitute a fixed
    window: `context_window_size` is 1_000_000 on this account's Opus sessions
    and `exceeds_200k_tokens` is nonetheless false, so that flag cannot stand in
    for the size.

    The counts are preferred over the sibling `used_percentage` only because
    they are exact; `used_percentage` is the fallback when a future version
    trims them.
    """
    window = status.get("context_window")
    if not isinstance(window, dict):
        return None

    size = window.get("context_window_size")
    usage = window.get("current_usage")
    if isinstance(size, int) and size > 0 and isinstance(usage, dict):
        # These three sum to exactly what the model was sent on the last turn.
        total = sum(
            value
            for key in (
                "input_tokens",
                "cache_creation_input_tokens",
                "cache_read_input_tokens",
            )
            if isinstance(value := usage.get(key), int)
        )
        if total:
            return min(100, round(total / size * 100))

    reported = window.get("used_percentage")
    if isinstance(reported, (int, float)):
        return min(100, round(reported))
    return None


def context_segment(percent: int) -> str:
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

    percent = context_percent(status)
    if percent is not None:
        segments.append(context_segment(percent))

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
