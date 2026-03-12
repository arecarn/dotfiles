# dotfiles

Personal configuration files managed with [dploy](https://github.com/arecarn/dploy)
and [invoke](https://www.pyinvoke.org/).

## Setup

```sh
uv sync
uv run inv stow       # symlink configs to $HOME
uv run inv provision  # install packages via ansible (Linux) or chocolatey (Windows)
```

## Tasks

| Task | Description |
|------|-------------|
| `stow` | Symlink dotfiles to home directory |
| `unstow` | Remove symlinks |
| `provision` | Install system packages |
| `lint` | Run shellcheck, yamllint, pylint, ruff |
