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

Two events reach this entry point, because a context window is built at two
moments, not one. `SessionStart` covers startup, resume, clear, and compact.
`SubagentStart` covers a spawned subagent, which gets its own fresh context and
fires no `SessionStart` -- without it a subagent sees no catalog at all and
falls back to whatever pointer the project's instructions happen to carry.

`SubagentStart` honours `additionalContext` (confirmed against Claude Code
2.1.251; the published hook reference omits it), and what it injects is visible
only to the subagent, not to the parent.
"""

import json
import pathlib
import sys

from manage.knowledge import cli, resolver

# Claude's own field name, nested per its hook protocol.
_DEFAULT_HOOK_EVENT = "SessionStart"
_HOOK_EVENTS = ("SessionStart", "SubagentStart")


def _event_name(event):
    """The event to answer, echoed back from the input Claude sent.

    Claude matches the reply against the event it fired, so answering a
    `SubagentStart` with `"SessionStart"` drops the context silently. An
    unrecognised name falls back rather than trusting the input verbatim.
    """
    name = event.get("hook_event_name") if isinstance(event, dict) else None
    return name if name in _HOOK_EVENTS else _DEFAULT_HOOK_EVENT


def _payload(context, event_name=_DEFAULT_HOOK_EVENT):
    """Claude's hook output shape, or an empty object for no context."""
    if not context:
        return {}
    return {
        "hookSpecificOutput": {
            "hookEventName": event_name,
            "additionalContext": context,
        }
    }


def session_start(stdin=None, stdout=None, config_dir=None):
    """Emit the knowledge catalog for the session or subagent Claude is starting.

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

    # No usable cwd means no catalog. Falling back to the process directory
    # would resolve against whatever Claude happened to launch the hook from,
    # which is the reason the input carries cwd in the first place.
    if not isinstance(event, dict) or not event.get("cwd"):
        json.dump(_payload(None), stdout)
        stdout.write("\n")
        return 0

    event_name = _event_name(event)
    cwd = pathlib.Path(event["cwd"])
    config_dir = config_dir or cli.resolve_config_dir(None)

    try:
        result = resolver.resolve(config_dir=config_dir, cwd=cwd)
        catalog = result.catalog
    except OSError:
        # A knowledge failure is never worth blocking a coding session over.
        catalog = None

    json.dump(_payload(catalog, event_name), stdout)
    stdout.write("\n")
    return 0
