# zinit plugin manager
ZINIT_HOME="${XDG_DATA_HOME:-$HOME/.local/share}/zinit/zinit.git"
if [[ ! -d "$ZINIT_HOME" ]]; then
    print -P "%F{blue}Installing zinit...%f"
    git clone https://github.com/zdharma-continuum/zinit.git "$ZINIT_HOME"
fi
source "$ZINIT_HOME/zinit.zsh"

# Completions (load early, before compinit)
zinit light zsh-users/zsh-completions

# Oh-my-zsh snippets (turbo-loaded)
zinit wait lucid for \
    OMZP::command-not-found \
    OMZP::tmux

# Turbo-loaded plugins (deferred)
zinit wait lucid for \
    zdharma-continuum/fast-syntax-highlighting

# zoxide (replaces rupa/z)
if (( $+commands[zoxide] )); then
    eval "$(zoxide init zsh)"
fi

# fzf
if [[ -f "${XDG_CONFIG_HOME:-$HOME/.config}/fzf/fzf.zsh" ]]; then
    source "${XDG_CONFIG_HOME:-$HOME/.config}/fzf/fzf.zsh"
elif [[ -f "$HOME/.fzf.zsh" ]]; then
    source "$HOME/.fzf.zsh"
fi

# fzf keybindings (set after plugins load)
_setup_fzf_bindings() {
    if (( $+commands[fzf] )); then
        bindkey -M viins '^T' fzf-file-widget
        bindkey -M viins '^Y' fzf-cd-widget
        bindkey -M viins '^R' fzf-history-widget
        FZF_COMPLETION_TRIGGER=**
    fi
}
_setup_fzf_bindings

ge() {
    local version=HEAD
    local files="$(git show --pretty="format:" --name-only "$version" | fzf)"
    [[ -n "$files" ]] && nvim "${files}"
}

# pyenv (if installed)
if [[ -d "$HOME/.pyenv" ]]; then
    export PYENV_ROOT="$HOME/.pyenv"
    export PATH="$PYENV_ROOT/bin:$PATH"
    eval "$(pyenv init -)"
elif (( $+commands[pyenv] )); then
    eval "$(pyenv init -)"
fi
