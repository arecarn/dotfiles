# Editor
if exists nvim; then
    export EDITOR='nvim'
else
    export EDITOR='vim'
fi

# Terminal color support
export COLORTERM=truecolor

export LANG='en_US.UTF-8'

# improved less option
export LESS='--tabs=4 --no-init --LONG-PROMPT --ignore-case --RAW-CONTROL-CHARS'

# configure path (prepend to take priority over inherited paths)
export PATH="${HOME}/.local/bin:${HOME}/bin:${PATH}"

if [[ "${OSTYPE}" == 'darwin'* ]]; then
    export MANPATH="${MANPATH}:/usr/local/man"
    export MANPATH="${MANPATH}:/opt/homebrew/bin"
    export PATH="/usr/local/bin:${PATH}"
    export PATH="/usr/local/opt/llvm/bin:${PATH}"
fi

if [[ ${TERM} == 'xterm' ]]; then
    export TERM=xterm-256color
fi

# Shortcuts to commonly used files/directories
zsh="${HOME}/.zshrc"
zshl="${HOME}/.zshrc_local"
shf="${SH_CONFIG_DIR}/functions.sh"
git="${HOME}/.gitconfig"
gitl="${HOME}/.gitconfig_local"
nvim="${HOME}/.config/nvim/init.lua"
tmux="${HOME}/.tmux.conf"
df="${HOME}/dotfiles/"
dfl="${HOME}/dotfiles_local/"
f="${HOME}/files/"
p="${f}/projects/"
n="${f}/notes/"
t="${n}/todo.txt"
i="${n}/inbox.md"
