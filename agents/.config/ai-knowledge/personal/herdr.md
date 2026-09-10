---
type: Playbook
title: Herdr workspace and agent orchestration
description: Everyday Herdr pane and agent operations, visible delegation and worktrees, and choosing between Herdr, pi-subagents, and pi-intercom
---
## Role in the toolchain

Herdr owns persistent terminal workspaces. A workspace contains tabs, and a tab
contains panes. A pane may hold a shell, an ordinary process, or a recognized
coding agent. Herdr tracks recognized agents as `idle`, `working`, `blocked`, or
`done` and exposes the same state through its local CLI.

Herdr is the right execution surface when the terminal itself matters: the user
can see it, attach to it, type into it, and keep it alive independently of the
calling agent session.

## Choose the smallest coordination surface

| Need | Use |
|------|-----|
| A governed child with bounded tools, structured results, worktree isolation, acceptance evidence, or workflow lanes | `pi-subagents` |
| A visible and attachable agent or process in its own persistent terminal | Herdr |
| A message or question for an existing Pi session | `pi-intercom` |
| Durable non-interactive shell work with retained logs | `pi-background-tasks` |

Herdr and `pi-subagents` are complementary. Visibility alone is not a reason to
replace the subagent workflow protocol, and an isolated subagent does not need a
new terminal pane. Prefer `pi-intercom` over terminal keystrokes when the target
is already a connected Pi session.

## Load the live command contract

The installed Herdr binary is authoritative because its CLI evolves. For an
agent-control task, first use the bundled skill when one is not already loaded:

```bash
herdr --skill
```

Use `herdr --help` and a command group such as `herdr agent` or `herdr pane` for
the current syntax. A bare `herdr` launches or attaches the TUI, so it is not a
help command.

Herdr control is scoped to a managed pane. Check that `HERDR_ENV=1` and use the
injected IDs rather than guessing which terminal is focused:

```bash
printf '%s\n' "$HERDR_WORKSPACE_ID" "$HERDR_TAB_ID" "$HERDR_PANE_ID"
```

Public handles have forms such as `w1`, `w1:t1`, and `w1:p1`. Creation and move
commands return the live IDs in JSON; carry those returned values forward.

## Inspect and navigate

Start with the semantic agent surface when a pane contains an agent:

```bash
herdr agent list
herdr agent get <name-or-pane-id>
herdr agent read <name-or-pane-id> --source recent-unwrapped --lines 120
herdr agent focus <name-or-pane-id>
```

Use the pane surface for terminals and ordinary processes:

```bash
herdr pane current --current
herdr pane list --workspace "$HERDR_WORKSPACE_ID"
herdr pane read <pane-id> --source recent-unwrapped --lines 120
```

`recent-unwrapped` is normally best for logs and transcripts. Agent and pane
reads do not mark background work as seen; focusing does.

## Delegate to a visible agent

Default to a sibling pane in the current tab and current directory. Keep the
user in the calling pane:

```bash
herdr pane split --current --direction right --cwd "$PWD" --no-focus
```

Read the new pane ID from `.result.pane.pane_id`, then start a supported agent
with a unique, useful name:

```bash
herdr agent start reviewer --kind pi --pane <new-pane-id>
herdr agent prompt reviewer \
  "Review the current diff and report only actionable findings." \
  --wait --timeout 120000
herdr agent read reviewer --source recent-unwrapped --lines 120
```

Use `down` instead of `right` when the current pane is narrow or tall. `agent
start` needs an existing shell pane; it does not create layout. Pass native agent
arguments after `--`.

A wait returning `blocked` means the agent needs human input. Read the pane to
show the exact question or approval before sending keys. A state of `unknown`
does not establish completion.

For an ordinary process, use the pane surface instead:

```bash
herdr pane run <pane-id> "make test"
herdr pane wait-output <pane-id> --match "test result" --timeout 120000
herdr pane read <pane-id> --source recent-unwrapped --lines 120
```

## Worktrees

Herdr can create or open Git worktree-backed workspaces:

```bash
herdr worktree list
herdr worktree create --help
herdr worktree open --help
```

Consult the live nested help before mutation. Use a Herdr worktree when a visible
terminal should own an independent checkout. Use managed `pi-subagents`
worktrees when isolation belongs to a governed child lane. Do not point two
concurrent writers at one checkout.

## Installed integration and local additions

Check integration state rather than caching versions:

```bash
herdr integration status
```

The official Pi integration reports lifecycle state and session identity. This
dotfiles setup adds two display integrations on top:

- Pi `/name` values are mirrored into the Herdr agent row and agent handle.
- Active Pi monitors, background tasks, and subagents appear as compact `M`, `B`,
  and `A` counts in that row.

Those additions are display-only. They do not replace Herdr's lifecycle
integration or provide an alternate orchestration protocol.

## Troubleshooting

Use the maintained upstream references instead of reconstructing detection or
socket behavior:

- First-time setup: <https://herdr.dev/agent-guide.md>
- Debugging and internals: <https://herdr.dev/llms.txt>
- Live control contract: `herdr --skill`

For a failed control operation, inspect `herdr status`, `herdr integration
status`, the target with `herdr agent get`, and its recent output. Preserve the
pane for inspection unless the user explicitly asked to close it.
