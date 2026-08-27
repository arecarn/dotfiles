"""Claude Code hook entry points for agent knowledge.

Claude Code calls a *command* per hook event, feeding it JSON on stdin and
reading JSON back on stdout. That command is a thin launcher under
`claude-code/.claude/plugins/`; the behaviour is here, where `inv lint` and the
tests reach it.

Two rules shape the output:

- The catalog goes into `hookSpecificOutput.additionalContext`, never into the
  user's prompt. It is context, not something the user said.
- A hook that fails must not fail the session. Every path exits 0, and an absent
  or broken configuration simply contributes no context.

`SessionStart` fires for startup, resume, clear, and compact, which is exactly
the set of moments Claude rebuilds what the model can see -- so it is the one
event this hook needs.
"""

import json
import pathlib
import sys

from manage.knowledge import cli, resolver

# Claude's own field name, nested per its hook protocol.
_HOOK_EVENT = "SessionStart"


def _payload(context):
    """Claude's SessionStart output shape, or an empty object for no context."""
    if not context:
        return {}
    return {
        "hookSpecificOutput": {
            "hookEventName": _HOOK_EVENT,
            "additionalContext": context,
        }
    }


def session_start(stdin=None, stdout=None, config_dir=None):
    """Emit the knowledge catalog for the session Claude is starting.

    `cwd` comes from the hook input rather than the process, because Claude may
    invoke the hook from elsewhere. Diagnostics are deliberately dropped: they
    name bundle paths, and this channel goes to the model.
    """
    stdin = stdin or sys.stdin
    stdout = stdout or sys.stdout

    try:
        event = json.load(stdin)
    except (json.JSONDecodeError, UnicodeDecodeError):
        event = {}

    cwd = pathlib.Path(event.get("cwd") or pathlib.Path.cwd())
    config_dir = config_dir or cli.config_dir(None)

    try:
        result = resolver.resolve(config_dir=config_dir, cwd=cwd)
        catalog = result.catalog
    except OSError:
        # A knowledge failure is never worth blocking a coding session over.
        catalog = None

    json.dump(_payload(catalog), stdout)
    stdout.write("\n")
    return 0
