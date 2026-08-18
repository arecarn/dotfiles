# Agent Context File

## Project Overview
This repository manages personal configuration files (dotfiles) across multiple operating systems, including Linux, Windows, and Termux. It provides an automated way to provision system packages and symlink configurations to the user's home directory.

- **Main Technologies:** Python, `uv` (package management), `invoke` (task running), `dploy` (symlink management), and `Ansible` (Linux provisioning).
- **Core Architecture:**
    - **Tool Configurations:** Located in root-level directories (e.g., `git/`, `nvim/`, `tmux/`, `zsh/`).
    - **Provisioning:** Ansible task files in `ansible/tasks/` for Linux systems, imported by `ansible/site.yml`.
    - **Task Automation:** `tasks.py` defines the CLI interface for management.

## Building and Running
The project uses `uv` for environment management. Tasks are executed via `invoke`.

| Task | Command | Description |
| :--- | :--- | :--- |
| **Setup Environment** | `uv sync` | Install Python dependencies. |
| **Stow Configurations**| `uv run inv stow` | Symlink dotfiles into the home directory using `dploy`. |
| **Unstow** | `uv run inv unstow` | Remove symlinks created by `stow`. |
| **Provision System** | `uv run inv provision` | Install system packages (Ansible on Linux, Chocolatey on Windows, pkg on Termux). |
| **Linting** | `uv run inv lint` | Run all linters (ShellCheck, yamllint, Pylint, Ruff, stylua, luacheck). |
| **Clean Repo** | `uv run inv clean` | Interactively clean untracked files using `git clean`. |

## Development Conventions
- **Cross-Platform Compatibility:** Logic in `tasks.py` detects the environment (Windows, Termux, Linux) to ensure tasks like `provision` and `stow` use the correct platform-specific tools.
- **Modular Provisioning:** Add a new tool as a task file in `ansible/tasks/`, then add an `ansible.builtin.import_tasks` line for it to the `tasks:` list in `ansible/site.yml`. A task file that nothing imports is never run, and provisioning still succeeds — so the omission is silent. Tag anything desktop-only with `desktop-only`, as `os-baseline.yml` and `wezterm.yml` do.
- **Symlink Strategy:** `dploy` is used to map stow package directories to the home directory. New stow packages must be added to the `Dploy` class in `tasks.py`.
- **This repo is public:** config that is private goes in a `dotfiles_local` repo instead — employer-internal hostnames, registries, proxies, project or team names, work email addresses, VPN or corporate tooling, and equally any personal config the user would not publish. A `dotfiles_local` exists per work or personal setup, and can span several machines. Keep what lands here public-safe and portable.
- **Windows symlink privilege:** stowing on Windows needs an elevated shell or Developer Mode — see [docs/gotchas/windows-symlink-creation-needs-elevation.md](docs/gotchas/windows-symlink-creation-needs-elevation.md).
- **Linting Standards:**
    - **Python:** `ruff` and `pylint`.
    - **Shell:** `shellcheck`.
    - **YAML:** `yamllint`.
    - **Lua:** `stylua` and `luacheck`.
- **Inventory Management:** Ansible inventory is managed in `ansible/hosts`. Local provisioning uses the `--inventory localhost` flag.
- **Watch CI after every push:** a green local run is not evidence — see [docs/gotchas/lint-passing-locally-proves-nothing-about-ci.md](docs/gotchas/lint-passing-locally-proves-nothing-about-ci.md) for why. Use the `watch-ci` skill, which selects the run by commit SHA and distinguishes a cancelled run from a failed one. CI here takes ~7 min.
- **Ansible on headless hosts:** gate desktop-only tasks with `failed_when: false` rather than `os_family` — see [docs/gotchas/desktop-only-ansible-tasks-fail-on-ci.md](docs/gotchas/desktop-only-ansible-tasks-fail-on-ci.md).

## Agent skills

### Issue tracker

Issues live as GitHub issues on `arecarn/dotfiles`, managed with the `gh` CLI. See `docs/agents/issue-tracker.md`.

### Triage labels

The five canonical triage roles used verbatim as label strings, plus a local `blocked` state and two closure reasons. Single-participant tracker, so parts of the skills' reporter model do not apply. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: one `CONTEXT.md` plus `docs/adr/` at the repo root, both created lazily. See `docs/agents/domain.md`.

### Gotchas

[docs/gotchas/](docs/gotchas/) holds non-obvious traps confirmed the hard way, so the same debugging is not paid for twice. Search with `grep -ri "<term>" docs/gotchas/`. The `record-gotcha` and `review-gotchas` skills drive writing and re-verifying entries.

- **One trap per file, named for the trap**, leading with the symptom you would grep for mid-debug. Deliberately unnumbered, unlike ADRs: entries are deleted when they stop reproducing, which would leave numbering gappy.
- **A gotcha is not an ADR.** Something *decided* — alternatives weighed, a call made — goes in `docs/adr/`. Something the system simply does, that nobody chose, goes here.
- **Every entry ends with a `**Confirmed:**` line** — the date it last reproduced and what against. Without it a live trap is indistinguishable from one fixed two years ago. Never backfill a date you cannot stand behind; write `unknown, predates this convention`.
- **Review on a trigger, not a calendar:** when a tool an entry names is upgraded, when its symptom recurs, or when you open it mid-debug and it does not help. Then update the `**Confirmed:**` line, or delete the entry if it no longer reproduces or a check now prevents it. **Deletion is the goal, not the failure case** — a trap engineered out of existence beats the best entry describing it.
