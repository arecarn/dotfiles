# A Claude Code hook script named *.sh gets `bash` prepended on Windows

Name a hook script `session-start.sh` and Windows runs it as
`bash session-start.sh`. That is fine for a shell script and wrong for anything
else: a Python hook is handed to bash, which fails on the first line it cannot
parse. The same file works on Linux, so it looks like a Windows-only break in a
script that has nothing platform-specific in it.

Claude Code's Windows auto-detection matches on the command *string* containing
`.sh`, not on the file's shebang.

The fix is to drop the extension. An extensionless `session-start` with a
`#!/usr/bin/env python3` shebang is invoked directly, and the shebang decides the
interpreter on both platforms:

```json
{
  "type": "command",
  "command": "\"${CLAUDE_PLUGIN_ROOT}/hooks/session-start\"",
  "shell": "bash"
}
```

Upstream plugins do the same thing for the same reason — the superpowers
marketplace ships `hooks/session-start` extensionless and says so in a comment,
so this is a known constraint rather than a local quirk.

Costs nothing on Linux, which is why it is worth doing unconditionally rather
than waiting until someone runs the hook on Windows.

**Confirmed:** 2026-08-27 against Claude Code 2.1.246, from the installed
`plugin-dev` hook-development skill and the extensionless hook scripts in the
superpowers marketplace.
