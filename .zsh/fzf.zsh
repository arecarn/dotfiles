# Setup fzf
# ---------
if [[ ! "$PATH" == */Users/arecarn/.fzf/fzf/bin* ]]; then
  export PATH="$PATH:/Users/arecarn/.fzf/fzf/bin"
fi

# Man path
# --------
if [[ ! "$MANPATH" == */Users/arecarn/.fzf/fzf/man* && -d "/Users/arecarn/.fzf/fzf/man" ]]; then
  export MANPATH="$MANPATH:/Users/arecarn/.fzf/fzf/man"
fi

# Auto-completion
# ---------------
[[ $- == *i* ]] && source "/Users/arecarn/.fzf/fzf/shell/completion.zsh" 2> /dev/null

# Key bindings
# ------------
source "/Users/arecarn/.fzf/fzf/shell/key-bindings.zsh"
