# Generate the Claude output style from the prose-style fragment

Prose voice rules live once, in `agents/.config/ai-instructions/prose-style.md`.
Pi receives them as part of its generated `AGENTS.md`. Claude Code receives them
instead as a generated output style at
`claude-code/.claude/output-styles/concise.md`, selected by
`_setup_claude_settings` in `tasks.py`. The fragment is deliberately absent from
`claude-code/.claude/CLAUDE.md`, so the rules reach Claude by exactly one route.

## Why

A Claude Code output style replaces the software-engineering-specific parts of
Claude's built-in system prompt, including its own brevity guidance. Context
files are additive: rules delivered through `CLAUDE.md` sit alongside those
defaults and have to argue with them. The bullet at risk is "expand when the
answer genuinely needs it", which is the one the defaults push against.

Delivering the same fragment to each harness in the form that harness actually
honors keeps one source of truth without giving up the replacement semantics.
The alternatives were worse:

- **Output style only** (the state before this): Claude-only, and reaching pi
  needed a second copy.
- **Fragment only, no style**: single-sourced, but Claude's built-in brevity
  instructions stay in force.
- **Hand-maintained style plus fragment**: two copies of the same rules to keep
  in sync, with nothing checking that they match.

The premise — that selecting an output style displaces those default prompt
sections — is from Claude Code's documentation, not verified on this machine;
the CLI ships no local docs to check. The observable symptom if it is wrong, or
stops being true, is Claude clipping the explanations the fragment licenses,
such as a tradeoff or root-cause walkthrough.

## Consequences

`instructions.py` grew a per-output `header`, emitted verbatim above the
generated banner, because an output style reserves the first line for YAML
frontmatter. It is the manifest's only entry needing one so far.

`_setup_claude_settings` writes `outputStyle: "Concise"` into
`~/.claude/settings.json`, so the generated file's name and its `name:`
frontmatter both matter: renaming either without the other leaves Claude
pointing at a style that does not exist. `lint-instructions` catches drift in
the file's content, not in that pairing.

Per-harness fragment selection now carries real weight. A fragment added to
every output *including* `claude-code/.claude/CLAUDE.md` will reach Claude twice
if it also belongs to the output style, so prose rules belong in exactly one of
those two lists.
