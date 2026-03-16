# fzf (source early so widgets are defined before syntax highlighting)
if (( $+commands[fzf] )); then
    source <(fzf --zsh)
fi

# Fix for fzf unhandled widgets in syntax highlighting
typeset -gA ZSH_HIGHLIGHT_WIDGETS_SKIP_REGEXP
ZSH_HIGHLIGHT_WIDGETS_SKIP_REGEXP+='|fzf-.*'

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
ZSH_TMUX_FIXTERM=false # terminal already set in ~/.tmux.conf
zinit wait lucid for \
    OMZP::command-not-found \
    OMZP::tmux \
    zsh-users/zsh-history-substring-search

# Turbo-loaded plugins (deferred)
zinit wait lucid for \
    zdharma-continuum/fast-syntax-highlighting

# zoxide
if (( $+commands[zoxide] )); then
    eval "$(zoxide init zsh --cmd cd)"
fi

# history-substring-search keybindings
_setup_history_substring_search_bindings() {
    bindkey '^[[A' history-substring-search-up
    bindkey '^[[B' history-substring-search-down
    bindkey -M vicmd 'k' history-substring-search-up
    bindkey -M vicmd 'j' history-substring-search-down
}
_setup_history_substring_search_bindings

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
