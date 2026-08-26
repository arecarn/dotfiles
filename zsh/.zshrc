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
    # herdr before tmux: whichever runs first claims the terminal, and each
    # declines when the other is already active. herdr is the default; tmux is
    # reached with NO_HERDR=1.
    "$ZSH_CONFIG_DIR/herdr.zsh"
    "$ZSH_CONFIG_DIR/tmux.zsh"
    "$ZSH_CONFIG_DIR/prompt.zsh"
    "$HOME/.zshrc_local"
)
# Use a namespaced loop variable: a plain `f` would clobber the `f` shortcut
# set in environment.zsh, which .zshrc_local expands.
for _zsh_src in "${zsh_sources[@]}"; do source_if_exists "$_zsh_src"; done
unset _zsh_src

# bob neovim version manager
export PATH="$HOME/.local/share/bob/nvim-bin:$PATH"

# Flow control
if [[ -t 0 ]]; then
    stty -ixon; stty stop undef
fi

# pnpm (global install shims land directly in $PNPM_HOME, not a bin/ subdir)
export PNPM_HOME="${HOME}/.local/share/pnpm"
if [[ -d "$PNPM_HOME" ]]; then
  case ":$PATH:" in
    *":$PNPM_HOME:"*) ;;
    *) export PATH="$PNPM_HOME:$PATH" ;;
  esac
fi
# pnpm end

# direnv
if command -v direnv &>/dev/null; then
  eval "$(direnv hook zsh)"
fi
