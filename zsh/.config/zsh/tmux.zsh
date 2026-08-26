# Auto-start tmux on interactive shells, when herdr has not already claimed the
# terminal. Sourced after herdr.zsh, so reaching this with no multiplexer running
# means herdr declined or is absent.
#
# Guards: interactive only, not already in tmux, not in a herdr pane, not in VS
# Code's integrated terminal, tmux installed.
#
# herdr is itself a multiplexer that spawns a shell per pane, so attaching here
# puts a shared tmux session inside every pane: each new pane joins the same
# session and redraws it, and herdr's own pane management ends up driving tmux
# windows instead of the shell it asked for. HERDR_ENV is exported into every
# pane's environment, so it identifies those shells the same way
# VSCODE_RESOLVING_ENVIRONMENT identifies VS Code's.
if [[ -o interactive ]] &&
    [[ -z "$TMUX" ]] &&
    [[ "$HERDR_ENV" != "1" ]] &&
    [[ -z "$VSCODE_RESOLVING_ENVIRONMENT" ]] &&
    command -v tmux &>/dev/null; then
    tmux attach 2>/dev/null || tmux new-session -s main
fi

# By default tmux updates the DISPLAY and SSH_AUTH_SOCK variables in tmux's
# own environment, so we have to propagate the environment to our shell.
if [ -n "$TMUX" ]; then
    tmux_refresh_env() {
        local val
        val=$(tmux show-environment SSH_AUTH_SOCK 2>/dev/null)
        [[ $val != -* && -n $val ]] && export "$val"
        val=$(tmux show-environment DISPLAY 2>/dev/null)
        [[ $val != -* && -n $val ]] && export "$val"

        if [[ -f "$HOME/.Xauthority" ]]; then
            # see https://kerneltalks.com/troubleshooting/mobaxterm-x11-proxy-authorisation-not-recognised/
            # This fixes authorization not recognized errors that prevents
            # opening graphical programs on a X-Server. The error is as follows:
            # > X11 proxy: Authorisation not recognised
            # > Error: Can't open display: localhost:10.0
            xauth add $(xauth -f "$HOME/.Xauthority" list | tail -1)
        fi
    }
else
    tmux_refresh_env() {
        # do nothing
    }
fi

# this is called after reading a command but before executing it
preexec() {
    tmux_refresh_env
}
