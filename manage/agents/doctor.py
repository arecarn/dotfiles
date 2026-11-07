"""Check that the commands Claude Code is configured to run still exist.

A hook or status line registered in `~/.claude/settings.json` outlives the file
it points at: deleting a feature from this repo does not touch the machine's
settings, and the harness reports the missing file on every session instead of
failing loudly once. `claude-setup` removes entries it knows about by name; this
catches the ones nobody listed.
"""

import json
import os
import pathlib
import shlex

from manage import repo


def _paths_in(command):
    """Absolute paths named in a shell command line, in order.

    Variable references are skipped: they are resolved by the harness at run
    time, so their existence cannot be judged from the settings file.
    """
    # posix=False on Windows keeps backslashes in paths rather than reading them
    # as escapes; the quotes it then leaves around a token are stripped below.
    tokens = shlex.split(command, posix=not repo.IS_WINDOWS)
    stripped = (token.strip("\"'") for token in tokens)
    return [t for t in stripped if os.path.isabs(t) and "$" not in t]


def _commands(settings):
    """Yield (where, command) for every command a settings file configures."""
    status_line = settings.get("statusLine", {})
    if "command" in status_line:
        yield "statusLine", status_line["command"]
    for event, entries in settings.get("hooks", {}).items():
        for entry in entries:
            for hook in entry.get("hooks", []):
                if "command" in hook:
                    yield f"hook {event}", hook["command"]


def missing_claude_commands(home=None):
    """Problems found in `~/.claude/settings.json`: one message per missing path.

    Empty when the file is absent or every referenced path exists.
    """
    base = pathlib.Path.home() if home is None else pathlib.Path(home)
    path = base / ".claude" / "settings.json"
    if not path.exists():
        return []
    settings = json.loads(path.read_text())
    return [
        f"{where} runs {missing}, which does not exist"
        for where, command in _commands(settings)
        for missing in _paths_in(command)
        if not pathlib.Path(missing).exists()
    ]


def report(problems):
    """Print `problems` with the cause and fix, and say whether any were found."""
    if not problems:
        return False
    print(f"Found {len(problems)} dead command(s) in ~/.claude/settings.json:")
    for problem in problems:
        print(f"  - {problem}")
    print(
        "A feature removed from the dotfiles leaves its hook behind; Claude Code "
        "then reports the missing file on every session. Delete the entry from "
        "~/.claude/settings.json, and add its command to "
        "manage/agents/settings.py's removed-hook cleanup so other machines "
        "shed it too."
    )
    return True
