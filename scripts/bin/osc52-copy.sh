#!/usr/bin/env bash
# osc52-copy.sh — copy text to the local clipboard via the OSC52 terminal escape.
#
# Writes the clipboard to whatever terminal emulator is driving the session,
# even over SSH or through tmux/screen. Robust to running inside a sandbox or
# subprocess that has no controlling tty of its own: it locates a terminal pty
# by inspecting fds, $SSH_TTY, and the process tree, then writes the escape
# there so the emulator performs the clipboard write.
#
# Usage:
#   osc52-copy.sh FILE          # copy file contents
#   osc52-copy.sh < FILE        # copy stdin
#   echo text | osc52-copy.sh   # copy stdin
#
# Options:
#   -t PTY        force target tty/pty (e.g. /dev/pts/11), skip detection
#   -p PROCNAME   prefer the tty of this ancestor process if found
#   -m            wrap for tmux passthrough (auto-enabled if $TMUX is set)
#   -q            quiet; no status line on success
#
# Exit codes: 0 ok, 1 usage error, 2 no pty found, 3 empty input.
set -euo pipefail

FORCE_PTY=""
PREFER_PROC=""
TMUX_WRAP=0
QUIET=0

while getopts ":t:p:mq" opt; do
  case "$opt" in
    t) FORCE_PTY="$OPTARG" ;;
    p) PREFER_PROC="$OPTARG" ;;
    m) TMUX_WRAP=1 ;;
    q) QUIET=1 ;;
    \?) echo "osc52-copy: unknown option -$OPTARG" >&2; exit 1 ;;
    :)  echo "osc52-copy: -$OPTARG needs an argument" >&2; exit 1 ;;
  esac
done
shift $((OPTIND - 1))

# --- read payload ----------------------------------------------------------
if [ $# -ge 1 ]; then
  [ -r "$1" ] || { echo "osc52-copy: cannot read '$1'" >&2; exit 1; }
  PAYLOAD=$(cat -- "$1")
else
  PAYLOAD=$(cat)
fi
[ -n "$PAYLOAD" ] || { echo "osc52-copy: empty input, nothing copied" >&2; exit 3; }

B64=$(printf '%s' "$PAYLOAD" | base64 | tr -d '\n')

# --- locate a terminal -----------------------------------------------------
proc_tty() {  # echo /dev/... for pid $1 if it has a real tty
  local t; t=$(ps -o tty= -p "$1" 2>/dev/null | tr -d ' ')
  [ -n "$t" ] && [ "$t" != "?" ] && echo "/dev/$t"
}

find_pty() {
  # 1) explicit override
  if [ -n "$FORCE_PTY" ]; then echo "$FORCE_PTY"; return; fi

  # 2) our own stdout / stderr, if they are terminals
  local fd p
  for fd in 1 2; do
    if [ -t "$fd" ]; then
      p=$(readlink "/proc/$$/fd/$fd" 2>/dev/null)
      case "$p" in /dev/*) echo "$p"; return ;; esac
    fi
  done

  # 3) preferred ancestor process by name
  local pid=$$ guard=0 comm t
  if [ -n "$PREFER_PROC" ]; then
    while [ "$pid" -gt 1 ] && [ "$guard" -lt 50 ]; do
      comm=$(ps -o comm= -p "$pid" 2>/dev/null || true)
      if [ "$comm" = "$PREFER_PROC" ]; then
        t=$(proc_tty "$pid") && { echo "$t"; return; }
        local link target
        for link in "/proc/$pid/fd/"*; do
          target=$(readlink "$link" 2>/dev/null) || continue
          case "$target" in /dev/pts/[0-9]*) echo "$target"; return ;; esac
        done
      fi
      pid=$(ps -o ppid= -p "$pid" 2>/dev/null | tr -d ' '); [ -n "$pid" ] || break
      guard=$((guard + 1))
    done
  fi

  # 4) first ancestor with any real tty. Inside a multiplexer this finds the
  #    pane pty (the layer the user is actually viewing), which is preferred
  #    over $SSH_TTY (the outer login tty the pane is nested inside).
  pid=$$ guard=0
  while [ "$pid" -gt 1 ] && [ "$guard" -lt 50 ]; do
    t=$(proc_tty "$pid") && { echo "$t"; return; }
    pid=$(ps -o ppid= -p "$pid" 2>/dev/null | tr -d ' '); [ -n "$pid" ] || break
    guard=$((guard + 1))
  done

  # 5) SSH_TTY of this session (fallback when no ancestor exposes a tty)
  if [ -n "${SSH_TTY:-}" ] && [ -w "$SSH_TTY" ]; then echo "$SSH_TTY"; return; fi

  # 6) fallback: newest pts I can write to (sort globbed paths by mtime)
  local newest="" cand
  for cand in /dev/pts/[0-9]*; do
    [ -w "$cand" ] || continue
    if [ -z "$newest" ] || [ "$cand" -nt "$newest" ]; then newest="$cand"; fi
  done
  [ -n "$newest" ] && { echo "$newest"; return; }
}

PTY=$(find_pty)
if [ -z "$PTY" ] || [ ! -w "$PTY" ]; then
  echo "osc52-copy: no writable terminal found" >&2; exit 2
fi

# --- emit escape -----------------------------------------------------------
SEQ=$(printf '\033]52;c;%s\007' "$B64")
[ -n "${TMUX:-}" ] && TMUX_WRAP=1
if [ "$TMUX_WRAP" -eq 1 ]; then
  # tmux passthrough: wrap in DCS so the outer terminal receives it.
  # ST (string terminator) is ESC + backslash; build via octal \134 to avoid
  # a literal backslash inside single quotes (SC1003).
  st=$(printf '\033\134')
  SEQ=$(printf '\033Ptmux;\033%s%s' "$SEQ" "$st")
fi

printf '%s' "$SEQ" > "$PTY"
[ "$QUIET" -eq 1 ] || echo "osc52-copy: ${#PAYLOAD} bytes copied via $PTY"
