# Auto-start herdr on interactive shells.
#
# Guards, in order of what they protect against:
#
#   HERDR_ENV      herdr exports this into every pane it spawns, and each of
#                  those shells sources this file. Without the guard, pane 1
#                  starts herdr, whose pane starts herdr, without bound. herdr
#                  also refuses to nest on its own ([experimental]
#                  allow_nested = false), so this is the first of two defenses
#                  rather than the only one.
#   TMUX           inside tmux, tmux won. Mirrors the HERDR_ENV guard in
#                  tmux.zsh, so whichever multiplexer starts first keeps the
#                  terminal and the other declines.
#   NO_HERDR       the deliberate opt-out: `NO_HERDR=1 zsh`, or exported in a
#                  terminal profile. This is how you reach a plain shell to
#                  start tmux, since an auto-started herdr would otherwise
#                  leave nowhere to type `tmux` from.
#   interactive    a script sourcing this file must not be handed a UI. Belongs
#                  with the guards rather than assumed from being in .zshrc.
#   VSCODE_...     VS Code drives its own terminal, as tmux.zsh already notes.
#
# Deliberately not `exec`: when herdr exits or you detach, the shell it was
# launched from is still there. Re-launching would make detaching impossible.
if [[ -o interactive ]] &&
    [[ "$HERDR_ENV" != "1" ]] &&
    [[ -z "$TMUX" ]] &&
    [[ -z "$NO_HERDR" ]] &&
    [[ -z "$VSCODE_RESOLVING_ENVIRONMENT" ]] &&
    command -v herdr &>/dev/null; then
    herdr
fi
