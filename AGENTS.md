# Agent Context File

## Project Overview
This repository manages personal configuration files (dotfiles) across multiple operating systems, including Linux, Windows, and Termux. It provides an automated way to provision system packages and symlink configurations to the user's home directory.

- **Main Technologies:** Python 3.10+, `uv` (package management), `invoke` (task running), `dploy` (symlink management), and `Ansible` (Linux provisioning).
- **Core Architecture:**
    - **Tool Configurations:** Located in root-level directories (e.g., `git/`, `nvim/`, `tmux/`, `zsh/`).
    - **Provisioning:** Modular Ansible roles in `ansible/roles/` for Linux systems.
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
- **Modular Provisioning:** New tools should be added as Ansible roles in `ansible/roles/` and included in `ansible/site.yml`.
- **Symlink Strategy:** `dploy` is used to map package directories to the home directory. New packages must be added to the `Dploy` class in `tasks.py`.
- **Windows symlink privilege:** Creating symlinks on Windows is privilege-gated — `inv stow` fails with `OSError: [WinError 1314] A required privilege is not held by the client` unless run elevated or with Developer Mode enabled (`Settings > For developers > Developer Mode`). Run stow from any elevated shell (admin terminal); `gsudo uv run inv stow` is a convenient inline way since `gsudo` is on PATH. Or enable Developer Mode once. Existing symlinks keep working without elevation; only *creating* them needs the privilege.
- **Linting Standards:**
    - **Python:** `ruff` and `pylint`.
    - **Shell:** `shellcheck`.
    - **YAML:** `yamllint`.
    - **Lua:** `stylua` and `luacheck`.
- **Inventory Management:** Ansible inventory is managed in `ansible/hosts`. Local provisioning uses the `--inventory localhost` flag.
