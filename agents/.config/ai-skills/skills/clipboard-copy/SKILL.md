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
clipboard write.

**Inside tmux** the script delegates to `tmux load-buffer -w` (tmux ≥3.2)
instead of emitting the escape itself. With `set-clipboard on` (the usual
config) tmux already intercepts inner OSC52 and re-emits it to the outer
terminal; hand-rolling the DCS passthrough wrap on top of that fights tmux and
leaks a stray glyph (e.g. `─`) into the pane. Letting tmux own the write is
the correct layer. The manual OSC52 emit is used only outside tmux (or when
`-t`/`-m` force manual control).

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

On success it prints `osc52-copy: N bytes copied via <target>`, where
`<target>` is `tmux load-buffer -w` inside tmux or `/dev/pts/X` otherwise. Tell
the user it's on their clipboard.

## Options

- `-t /dev/pts/N` — force the target tty/pty, skip detection.
- `-p NAME` — prefer the tty of this ancestor process (e.g. `-p claude`) if the
  generic walk picks the wrong one.
- `-m` — force the manual tmux DCS passthrough wrap instead of the
  `tmux load-buffer -w` fast path. Rarely needed; only if the tmux native path
  is unavailable or misbehaving.
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

## If a stray glyph leaks into the pane (e.g. `─`)

That's a mangled DCS passthrough escape reaching the screen instead of the
clipboard — the manual OSC52 wrap colliding with tmux's own clipboard handling.
The script now avoids this inside tmux by using `tmux load-buffer -w`. If you
still see it, you likely forced manual mode with `-m` (or `-t`); drop the flag
so the tmux fast path runs. Confirm with `tmux -V` that tmux is ≥3.2.

## Limits

- Some terminals cap OSC52 payload size; very large pastes may truncate. Warn
  the user when copying something big.
- Uses the `c` (clipboard) target only — no primary-selection variant.
