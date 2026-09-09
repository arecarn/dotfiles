"""Claude Code hook: publish a running-subagent count to the pane's herdr row.

Claude Code runs this on four hook events -- SessionStart, SubagentStart,
SubagentStop, SessionEnd -- passing the event as a JSON object on stdin. The
script keeps a per-session list of live subagent ids in a state file under
$XDG_RUNTIME_DIR and, when running inside a herdr pane, republishes an `A<n>`
token on the pane's sidebar row after every change (no token when n is 0).

Inert outside herdr: with HERDR_ENV != "1" or HERDR_PANE_ID unset it returns
before touching the filesystem or herdr. A display token must never break a
hook, so every path returns 0 and the herdr call's failures are swallowed.

Not linted (its directory is out of the repo lint set, like statusline.py);
covered by tests/test_herdr_work_status.py.
"""

from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys
import time

# herdr namespaces a source's writes so it can expire or override them
# independently; this is ours.
SOURCE = "claude-work-status"
TOKEN = "work_status"
HERDR_TIMEOUT_S = 5
# Generous upper bound on the state file; it holds only a list of uuids.
_STATE_READ_BYTES = 1 << 20


def format_token(count: int) -> str | None:
    """The token value for `count` running subagents, or None to clear it."""
    return f"A{count}" if count > 0 else None


def next_state(state: dict, event: object) -> dict:
    """Return the state after applying one hook `event`.

    `state` is `{"agents": [agent_id, ...]}`, the list used as an ordered set.
    An unknown id on SubagentStop is ignored, so a missed SubagentStart cannot
    drive the count below zero. A malformed event leaves the list unchanged.
    """
    agents = list(state.get("agents", [])) if isinstance(state, dict) else []
    if not isinstance(event, dict):
        return {"agents": agents}

    name = event.get("hook_event_name")
    agent_id = event.get("agent_id")
    if name == "SubagentStart" and agent_id is not None and agent_id not in agents:
        agents.append(agent_id)
    elif name == "SubagentStop" and agent_id in agents:
        agents.remove(agent_id)
    elif name in ("SessionStart", "SessionEnd"):
        agents = []
    return {"agents": agents}


def _state_path(session_id: str) -> pathlib.Path:
    root = os.environ.get("XDG_RUNTIME_DIR") or "/tmp"  # fallback only
    return pathlib.Path(root) / "herdr-claude-work" / f"{session_id}.json"


def _update_and_publish(path: pathlib.Path, event: dict, pane_id: str) -> dict:
    """Read-modify-write the state file, then publish the token, under one lock.

    Returns the new state `{"agents": [...]}`. The `--seq` sample and the herdr
    call happen while the exclusive lock is still held, so sibling start/stop
    hooks -- which can fire at the same moment, each in its own process --
    publish in the same order they mutated the state, never leaving a stale
    count until the next event. The herdr subprocess is fast and the hook has a
    15s budget, so holding the lock across it is acceptable.
    """
    # POSIX-only; main()'s inert guard returns before this on Windows
    import fcntl

    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_RDWR | os.O_CREAT, 0o644)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        raw = os.read(fd, _STATE_READ_BYTES).decode() or "{}"
        try:
            current = json.loads(raw)
        except ValueError:
            current = {"agents": []}  # a corrupt or truncated state file is treated as empty
        updated = next_state(current, event)
        os.lseek(fd, 0, os.SEEK_SET)
        os.ftruncate(fd, 0)
        os.write(fd, json.dumps(updated).encode())
        _publish(pane_id, format_token(len(updated["agents"])))
        return updated
    finally:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)


def _publish(pane_id: str, token_value: str | None) -> None:
    herdr = os.environ.get("HERDR_BIN_PATH") or "herdr"
    args = [
        herdr, "pane", "report-metadata", pane_id,
        "--source", SOURCE,
        "--seq", str(time.time_ns()),
    ]
    if token_value is None:
        args += ["--clear-token", TOKEN]
    else:
        args += ["--token", f"{TOKEN}={token_value}"]
    try:
        subprocess.run(
            args, timeout=HERDR_TIMEOUT_S, check=False, capture_output=True
        )
    except (OSError, subprocess.SubprocessError):
        pass  # display-only status must never disrupt the session


def main() -> int:
    try:
        event = json.load(sys.stdin)
    except (ValueError, OSError):
        return 0
    if not isinstance(event, dict):
        return 0

    if os.environ.get("HERDR_ENV") != "1":
        return 0
    pane_id = os.environ.get("HERDR_PANE_ID")
    if not pane_id:
        return 0
    session_id = event.get("session_id")
    if not session_id:
        return 0

    path = _state_path(str(session_id))
    try:
        _update_and_publish(path, event, pane_id)
    except OSError:
        return 0

    if event.get("hook_event_name") == "SessionEnd":
        path.unlink(missing_ok=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
