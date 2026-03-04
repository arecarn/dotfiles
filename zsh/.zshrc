# Directories (XDG)
export ZSH_DATA_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/zsh"
export ZSH_CACHE_DIR="${XDG_CACHE_HOME:-$HOME/.cache}/zsh"
export ZSH_CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/zsh"
export SH_CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/shell"
mkdir -p "$ZSH_DATA_DIR" "$ZSH_CACHE_DIR"

# Shell (before plugins)
export SHELL=/usr/bin/zsh

# Shared functions
source "$SH_CONFIG_DIR/functions.sh"

# Cargo (before PATH setup)
[[ -f "$HOME/.cargo/env" ]] && . "$HOME/.cargo/env"

# bob neovim version manager
export PATH="$HOME/.local/share/bob/nvim-bin:$PATH"

# Load modules
for module in plugins environment options keybindings aliases tmux prompt; do
    [[ -f "$ZSH_CONFIG_DIR/$module.zsh" ]] && source "$ZSH_CONFIG_DIR/$module.zsh"
done

# Flow control
stty -ixon; stty stop undef

# Local overrides
[[ -f "$HOME/.zshrc_local" ]] && source "$HOME/.zshrc_local"
