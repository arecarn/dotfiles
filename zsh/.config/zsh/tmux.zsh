# By default tmux updates the DISPLAY and SSH_AUTH_SOCK variables in tmux's
# own environment, so we have to propagate the environment to our shell.
if [ -n "$TMUX" ]; then
    tmux_refresh_env() {
        export $(tmux show-environment | grep "^SSH_AUTH_SOCK") > /dev/null
        export $(tmux show-environment | grep "^DISPLAY") > /dev/null

        if [[ -f "~/.Xauthority" ]]; then
            # see https://kerneltalks.com/troubleshooting/mobaxterm-x11-proxy-authorisation-not-recognised/
            # This fixes authorization not recognized errors that prevents
            # opening graphical programs on a X-Server. The error is as follows:
            # > X11 proxy: Authorisation not recognised
            # > Error: Can't open display: localhost:10.0
            xauth add $(xauth -f ~/.Xauthority list | tail -1)
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
