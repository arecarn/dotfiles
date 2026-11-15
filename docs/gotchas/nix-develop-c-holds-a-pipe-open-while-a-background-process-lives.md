# `nix develop -c` keeps a pipe open until every background process it started exits

**`nix develop <flake> -c <cmd> | cat` (or any caller capturing output through
a pipe) does not return when `<cmd>` leaves a daemon running, even though
`<cmd>` itself exited and printed everything.** `paseo-emulator start` and an
`adb` server are the daemons that trigger it here: the caller waits for the
emulator's whole lifetime.

Nix's crash handler (`crashpad_handler`) inherits the caller's stdout and
stays alive while anything started in the session lives. Redirecting the
daemon's own stdio and closing the inherited lock descriptor (fd 3) did not
help, so it cannot be fixed inside the helper.

Run it from an interactive `nix develop` shell, through `direnv exec`, or send
the one-shot's output to a file (`> out.log 2>&1`) instead of a pipe.

**Confirmed:** 2026-11-14, Determinate Nix 3.24.2: `nix develop -c bash -c
'setsid sleep 20 >/dev/null 2>&1 </dev/null & echo started' | cat` printed
`started` and returned after 21 seconds; the same with output to a file
returned at once.
