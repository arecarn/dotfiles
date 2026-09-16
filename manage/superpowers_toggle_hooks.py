"""Claude Code SessionStart hook: best-effort note when the bootstrap is off.

Superpowers registers its own SessionStart hook from inside its installed
plugin directory (~/.claude/plugins/cache/superpowers-dev/...), not from
anything this repo stows. Claude Code merges hook entries from every source
that registers one; it does not let a second hook replace or cancel the
first. So there is no way from here to suppress superpowers' own
"You have superpowers" block -- only to add an instruction after it.

That means this hook is not a suppression, only a note asking the model to
disregard the block it already received. It exists so flipping the shared
flag has some effect in Claude even though it cannot have the pi extension's
effect. See docs/adr/ for why a real toggle is not possible here, and
manage/superpowers_toggle.py for the flag both harnesses read.

Every path exits 0: a hook failing must not fail the session, same rule as
manage/knowledge/hooks.py.
"""

import json
import sys

from manage import superpowers_toggle

_DISABLED_NOTE = (
    "The superpowers-toggle flag is currently off. If a 'You have superpowers' "
    "bootstrap block appears in this context, disregard its instructions: "
    "treat superpowers skills as available on request, not mandatory. This is "
    "a best-effort note, not a suppression -- see manage/superpowers_toggle.py."
)


def _payload(context):
    if not context:
        return {}
    return {
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": context,
        }
    }


def session_start(stdin=None, stdout=None, state_dir=None):
    """Emit a disregard note when the shared flag is off; nothing otherwise."""
    stdin = stdin or sys.stdin
    stdout = stdout or sys.stdout

    try:
        json.load(stdin)
    except (json.JSONDecodeError, UnicodeDecodeError):
        pass

    context = None if superpowers_toggle.is_enabled(state_dir) else _DISABLED_NOTE

    json.dump(_payload(context), stdout)
    stdout.write("\n")
    return 0
