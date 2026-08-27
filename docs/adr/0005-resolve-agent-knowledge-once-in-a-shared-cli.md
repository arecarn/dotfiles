# Resolve agent knowledge once, in a shared CLI

`manage/knowledge/` decides which OKF knowledge bundles apply in a directory, and
the `agent-knowledge` command is the only way the three harness adapters ask. The
pi extension, the Claude Code plugin, and the OpenCode plugin each translate one
JSON answer into their own lifecycle; none of them knows an activation rule.

## Why

Reference material had nowhere to live but the generated instruction files, which
every session loads whole. Splitting it into OKF bundles needs an answer to
"which bundles apply here", and that answer is not obvious: it depends on the
working directory, a public and a private config file, and whether the current
worktree carries its own `agents-knowledge/`.

Three harnesses would otherwise each answer it. They disagree about almost
everything else -- pi loads TypeScript extensions, Claude Code runs command
hooks, OpenCode loads JavaScript plugins -- so three implementations of the same
rules would drift, and the drift would be silent: a bundle that stops appearing
looks exactly like a bundle that was never configured.

A process boundary is the only contract all three can share. None of them can
import Python, so JSON on stdout is what is left.

## Consequences

**The CLI must run under a bare `python3`.** A harness hook does not inherit this
repo's venv, so `manage.knowledge` imports no third-party module unconditionally:
`manage/__init__.py` deliberately imports nothing, and `config.py` accepts
ruamel.yaml or PyYAML and treats neither as required. Importing `manage.agents`
from here would make every hook depend on this repo's own dependencies.

**Exit codes are the adapters' control flow,** not shell convention: 0 for a
usable answer (including "no bundles" and "your config is broken"), 1 for a
refused read, 2 for a bad invocation. A malformed config file must never fail the
session that asked, so it exits 0 with a diagnostic.

**Adapters hardcode the install path.** `scripts/bin/agent-knowledge` stows to
`~/bin`, and each adapter invokes it there by absolute path because a hook has no
shell. Getting that path wrong fails silently -- an absent CLI is indistinguishable
from no knowledge configured -- so `tests/test_knowledge_launcher.py` asserts the
adapters and `manage.stow` still agree.

**Three fold barriers were added** to `manage/stow.py`: `~/.config/ai-knowledge`
(a `dotfiles_local` repo drops `bundles_local.yaml` beside our `bundles.yaml`,
and folding would put that private file in this public repo),
`~/.claude/plugins`, and `~/.config/opencode/plugins` (each holds one plugin of
ours beside whatever else is installed). Same reasoning as ADR-0001.

**Only root indexes reach a model.** The catalog quotes each active bundle's
`index.md` and nothing else; concepts are read on request through the same CLI.
That is the whole point -- a large corpus should cost a catalog, not a context
window -- and it is why the reader is constrained rather than a plain file read:
a bundle may sit outside the workspace the harness would otherwise allow.

**Model-facing output never names a path.** Only `status` does, and it is routed
to the local user. An inactive work bundle's location is exactly the kind of
detail that must not reach a model or a transcript, so inactive bundles are not
even opened during resolution.

Rejected: a library each adapter vendors (two of three cannot run Python), an
MCP server (a server to run and authenticate for a local file read), and
per-harness logic (the drift this exists to prevent).
