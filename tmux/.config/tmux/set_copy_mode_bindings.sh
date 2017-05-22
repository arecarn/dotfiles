#/bin/sh

versionlt() {
    version=$(tmux -V | cut -c 6-)
    [ "$(echo "${version} < $1" | bc)" = 1 ]
}

if  versionlt "2.4"; then
    tmux bind-key -t vi-copy v begin-selection
    tmux bind-key -t vi-copy V rectangle-toggle
    tmux bind-key -t vi-copy y copy-selection
    tmux bind-key -t vi-copy | start-of-line
else
    tmux bind-key -T copy-mode-vi 'v' send-keys -X begin-selection
    tmux bind-key -T copy-mode-vi 'V' send-keys -X rectangle-toggle
    tmux bind-key -T copy-mode-vi 'y' send-keys -X copy-selection
    tmux bind-key -T copy-mode-vi '|' send-keys -X start-of-line
fi
