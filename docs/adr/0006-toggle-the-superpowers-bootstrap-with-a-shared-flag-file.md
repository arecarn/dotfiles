# Toggle the superpowers bootstrap with a shared flag file

`manage/superpowers_toggle.py` holds one on/off flag under `~/.local/state/ai-skills/`.
A pi extension and a Claude Code hook each read it to decide whether to let
obra/superpowers' "You have superpowers" bootstrap prompt through, and a
`superpowers-toggle` CLI (stowed to `~/bin`) flips it from either harness's
shell. pi gets a real mid-session toggle; Claude Code gets a same-session
best-effort note, for reasons below.

## Why

obra/superpowers injects an `<EXTREMELY_IMPORTANT>` block instructing the model
to follow its workflow, and ships no setting to turn that off -- only
`SUPERPOWERS_DISABLE_TELEMETRY`, which governs unrelated visual-companion
telemetry. The only way to silence it is removing the package from
`~/.pi/agent/settings.json` or disabling the Claude plugin via `enabledPlugins`,
both of which also remove every superpowers skill (brainstorming,
systematic-debugging, TDD, and the rest) that the injection exists to advertise.
That all-or-nothing tradeoff is what this ADR avoids.

## pi: the injection point is a real seam

Pi calls every extension's `context` handler before each LLM request
(`transformContext` -> `emitContext` in `@earendil-works/pi-agent-core`), chained:
each handler sees the previous handler's output, in extension load order.
Extensions auto-discovered from `~/.pi/agent/extensions/` (user scope) load
before a package's own extensions (package scope) -- confirmed from
`resourcePrecedenceRank` in pi's `package-manager.js`, where `package` ranks
below every user and project source. So `pi/.pi/agent/extensions/superpowers-toggle.ts`
runs before superpowers' own `.pi/extensions/superpowers.ts` on every call.

Superpowers' injector has a documented escape hatch: it checks whether any
message already contains the marker string
`superpowers:using-superpowers bootstrap for pi` and skips injecting if so. When
the shared flag is off, this extension's `context` handler seeds a small decoy
message carrying that exact marker, so superpowers' own handler -- running
right after, seeing the mutated message list -- stands down. `/superpowers-toggle`
(and `[on|off]`) flips the same flag file pi's own extension reads, so the effect
is visible on the very next LLM call: no restart, no new session.

**What this does not do:** retract a bootstrap block already sent to the model
this session. Pi's context injection is not persisted into session state --
`emitContext` builds it fresh from a deep-cloned copy of `event.messages` for
each call -- so there is nothing stored to strip once a call has gone out. The
toggle prevents the *next* injection; it was never going to be able to unsend
one already delivered. Superpowers only injects once per session (again after
compaction) in the first place, per its own `injectBootstrap` flag
(true at `session_start`/`session_compact`, false after `agent_end`), so "before
the next injection point" in practice means "before your first message, or
before the next compaction."

## Claude Code: no seam exists

Superpowers registers its `SessionStart` hook from inside its own installed
plugin directory (`~/.claude/plugins/cache/superpowers-dev/superpowers/<version>/hooks/`),
via that plugin's own `hooks.json` -- not through anything this repo stows or
owns. Claude Code's hook system merges every source's `SessionStart` entries and
runs all of them; there is no mechanism for a second hook to cancel, replace, or
run conditionally-before another plugin's hook. The only native lever that stops
superpowers' output entirely is `enabledPlugins: false` for the whole plugin,
which is the all-or-nothing tradeoff this ADR exists to avoid.

`manage/superpowers_toggle_hooks.py` therefore does not suppress anything. It
registers its own `SessionStart` hook (`agents/bin/superpowers-toggle-session-start`,
wired in `manage/agents/settings.py` next to the knowledge and work-status hooks)
that, when the flag is off, appends an instruction asking the model to disregard
whatever bootstrap block it already received and treat superpowers skills as
available on request rather than mandatory. This is a counter-prompt, the same
category of fix rejected for pi during design (fighting one injected instruction
with another, with no guarantee the model weighs the second one higher) --
accepted here only because pi's real seam does not exist on this side, and a
best-effort note plus a working `pi` toggle beats leaving Claude untouched.

**Considered and rejected:** patching the vendored `hooks/session-start` script
in place. It would actually suppress the output, but it edits a third-party
plugin's installed files outside version control and outside this repo's stow
model, and `claude plugin update` (or the manifest's Claude install/update
commands) overwrites it silently, reverting the toggle with no error. Revisit if
Claude Code ever exposes per-hook enable/disable or a way for one plugin's hook
to suppress another's.

## Consequences

**One flag, read by both harnesses and the CLI**, under `~/.local/state/ai-skills/superpowers-bootstrap`
(state, not `~/.config` -- this is a human-flipped runtime toggle, not declared
configuration). Absent file means enabled, so a machine that never touches the
toggle behaves exactly as superpowers ships.

**The pi-side marker string is duplicated, not imported.** Pi packages load with
separate module roots (`docs/packages.md`), so there is no shared module between
this repo's extension and superpowers' package to import the constant from. A
future superpowers release renaming `BOOTSTRAP_MARKER` silently re-enables its
bootstrap in pi until this file is updated to match.

**The Claude-side hook is best-effort by construction**, not a bug to fix later
within this design -- fixing it for real needs a Claude Code capability that does
not exist yet (see rejected alternative above).
