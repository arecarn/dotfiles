---
name: clipboard-copy
description: Copy text to the user's local clipboard via the OSC52 terminal escape, even from a sandboxed/headless shell with no controlling tty. Use when the user says "copy this to my clipboard", "copy to clipboard", "osc52", "put this on my clipboard", or wants generated text (a draft, snippet, command, summary) placed on their clipboard.
host: any
---

# clipboard-copy

Copy arbitrary text to the user's local clipboard using the OSC52 escape
sequence. The harness runs Bash in a sandbox with no controlling tty, so
`/dev/tty` fails and stdout is captured (the escape never reaches the
terminal). The `osc52-copy.sh` script handles this: it finds the terminal pty
driving the session and writes the escape there, so the emulator performs the
clipboard write. It also auto-wraps for tmux passthrough.

## Usage

`osc52-copy.sh` is on `PATH`. Write the payload to a temp file first (avoids
quoting/escaping issues with multi-line or markdown content), then pass it:

```bash
cat > /tmp/clip.txt << 'EOF'
<content to copy>
EOF
osc52-copy.sh /tmp/clip.txt
```

Or pipe stdin:

```bash
echo "some text" | osc52-copy.sh
```

On success it prints `osc52-copy: N bytes copied via /dev/pts/X`. Tell the user
it's on their clipboard.

## Options

- `-t /dev/pts/N` — force the target tty/pty, skip detection.
- `-p NAME` — prefer the tty of this ancestor process (e.g. `-p claude`) if the
  generic walk picks the wrong one.
- `-m` — force tmux DCS passthrough wrap (auto-enabled when `$TMUX` is set).
- `-q` — quiet, no status line.

## How it finds the terminal

In order: `-t` override → own stdout/stderr if a tty → `-p` ancestor →
first ancestor process with a real tty (inside tmux/screen this is the pane the
user is viewing, preferred over `$SSH_TTY`) → `$SSH_TTY` → newest writable
`/dev/pts/*`.

## If the clipboard stays empty

The terminal emulator has OSC52 clipboard-write disabled. Common fixes:
- **tmux**: `set -g set-clipboard on` (and `set -g allow-passthrough on`)
- **iTerm2**: Settings → General → Selection → "Applications in terminal may
  access clipboard"
- **kitty / wezterm / alacritty / ghostty**: enabled by default

## Limits

- Some terminals cap OSC52 payload size; very large pastes may truncate. Warn
  the user when copying something big.
- Uses the `c` (clipboard) target only — no primary-selection variant.
