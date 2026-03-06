# Directories (XDG)
export ZSH_DATA_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/zsh"
export ZSH_CACHE_DIR="${XDG_CACHE_HOME:-$HOME/.cache}/zsh"
export ZSH_CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/zsh"
export SH_CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/shell"
mkdir -p "$ZSH_DATA_DIR" "$ZSH_CACHE_DIR"

source_if_exists() { [[ -f "$1" ]] && source "$1"; }

zsh_sources=(
    "$SH_CONFIG_DIR/functions.sh"
    "$HOME/.cargo/env"
    "$ZSH_CONFIG_DIR/plugins.zsh"
    "$ZSH_CONFIG_DIR/environment.zsh"
    "$ZSH_CONFIG_DIR/options.zsh"
    "$ZSH_CONFIG_DIR/keybindings.zsh"
    "$ZSH_CONFIG_DIR/aliases.zsh"
    "$ZSH_CONFIG_DIR/tmux.zsh"
    "$ZSH_CONFIG_DIR/prompt.zsh"
    "$HOME/.zshrc_local"
)
for f in "${zsh_sources[@]}"; do source_if_exists "$f"; done

# bob neovim version manager
export PATH="$HOME/.local/share/bob/nvim-bin:$PATH"

# Flow control
stty -ixon; stty stop undef
