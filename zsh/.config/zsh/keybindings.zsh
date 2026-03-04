# vi like settings
bindkey -v
export KEYTIMEOUT=1

# Vim Mode (Ins Mode)
_backward-kill-word-and-split-undo() {
    zle backward-kill-word
    zle split-undo
}
zle -N _backward-kill-word-and-split-undo

_backward-kill-line-and-split-undo() {
    zle backward-kill-line
    zle split-undo
}
zle -N _backward-kill-line-and-split-undo

_backward-delete-char-and-split-undo() {
    zle backward-delete-char
    zle split-undo
}
zle -N _backward-delete-char-and-split-undo

_insert-next-word() {
    zle insert-last-word 1
}
zle -N _insert-next-word

autoload -Uz edit-command-line
zle -N edit-command-line

zle -C complete-menu menu-select _generic
_complete_menu() {
    setopt localoptions alwayslastprompt
    zle complete-menu
}
zle -N _complete_menu


bindkey -M viins '^A'    beginning-of-line
bindkey -M viins '^E'    end-of-line
bindkey -M viins '^Y'    kill-line
bindkey -M viins '^P'    history-beginning-search-backward
bindkey -M viins '^N'    history-beginning-search-forward
bindkey -M viins '^/'    undo
bindkey -M viins '^W'    _backward-kill-word-and-split-undo
bindkey -M viins '^U'    _backward-kill-line-and-split-undo
bindkey -M viins '^H'    _backward-delete-char-and-split-undo
bindkey -M viins '^?'    _backward-delete-char-and-split-undo
bindkey -M viins '^X'    _expand_alias
bindkey -M viins '^K'    insert-last-word
bindkey -M viins '^O'    _insert-next-word
bindkey -M viins '^S'    copy-prev-shell-word
bindkey -M viins '^X^R'  redisplay
bindkey -M viins '\eOH'  beginning-of-line # Home
bindkey -M viins '\eOF'  end-of-line # End
bindkey -M viins '\e[2~' overwrite-mode # Insert
bindkey -M viins '^F'    forward-char
bindkey -M viins '^B'    backward-char
bindkey -M viins '^V'    edit-command-line
bindkey -M viins '^G'    _complete_menu
bindkey -M viins '^Q'    push-line

# Vim Mode (Cmd Mode)
bindkey -M vicmd '^A'    beginning-of-line
bindkey -M vicmd '^E'    end-of-line
bindkey -M vicmd '^P'    history-beginning-search-backward
bindkey -M vicmd '^N'    history-beginning-search-forward
bindkey -M vicmd '^K'    kill-line
bindkey -M vicmd '^Y'    yank
bindkey -M vicmd '^W'    backward-kill-word
bindkey -M vicmd '^U'    backward-kill-line
bindkey -M vicmd '/'     history-incremental-pattern-search-backward
bindkey -M vicmd '?'     history-incremental-pattern-search-forward
bindkey -M vicmd '^/'    undo
bindkey -M vicmd u       undo
bindkey -M vicmd '^R'    redo
bindkey -M vicmd '^F'    forward-char
bindkey -M vicmd '^B'    backward-char
bindkey -M vicmd g~      vi-oper-swap-case
bindkey -M vicmd gg      beginning-of-buffer-or-history
bindkey -M vicmd G       end-of-buffer-or-history
bindkey -M vicmd '^V'    edit-command-line
bindkey -M vicmd '^Q'    push-line

# Menu Selection
bindkey -M menuselect '^S' history-incremental-search-forward
bindkey -M menuselect '^R' history-incremental-search-backward
bindkey -M menuselect '^?' backward-delete-char
bindkey -M menuselect '^/' undo
bindkey -M menuselect '^[[Z' reverse-menu-complete # Shift Tab
bindkey -M menuselect '^Y' accept-and-infer-next-history
bindkey -M menuselect '^N' down-line-or-history
bindkey -M menuselect '^P' up-line-or-history
bindkey -M menuselect '^B' backward-char
bindkey -M menuselect '^F' forward-char
