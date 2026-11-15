# The Paseo desktop app never maps a window under Xvfb on a Wayland session

**Under Xvfb the full Electron app (`npm run dev:desktop`) leaves the root
window black for minutes, even with `--disable-gpu`, `ELECTRON_DISABLE_SANDBOX=1`
and `WAYLAND_DISPLAY` unset. `xwininfo -root -tree` lists no application
window.**

Electron 44 chooses its Ozone backend from `XDG_SESSION_TYPE=wayland`, even
when `WAYLAND_DISPLAY` is empty or unset, so the browser process tries Wayland
and never creates an X window. The GPU process still logs
`--ozone-platform=x11` (the flag reaches child processes), which hides the
fault. A flag set from the app's JavaScript (`PASEO_ELECTRON_FLAGS`) is too
late for the browser process, and `ELECTRON_OZONE_PLATFORM_HINT=x11` had no
effect. Unset the session variable before Electron starts:

```sh
env -u WAYLAND_DISPLAY -u XDG_SESSION_TYPE xvfb-run -a ... npm run dev:desktop
```

The dev shell's `paseo-desktop-shot` does this and returns a PNG of the real
window. `paseo-desktop-capture` is unaffected: it passes `--ozone-platform=x11`
on the command line and screenshots through `capturePage`, not the X server.

Two things look like the same fault and are not:

- The main window is created hidden and shown on `did-finish-load`, so no
  window exists until Metro has served the web bundle. The first bundle of a
  checkout takes minutes; later runs show the window after about a minute.
- A `login-shell-env` timeout of about 35 s at startup is harmless here.

**Confirmed:** 2026-11-14, Paseo `origin/main` (Electron 44.2.0) on Ubuntu
26.04, Wayland session, Xvfb 21.1: root mean 0 for 420 s with the Wayland
default and with `--ozone-platform=x11` in `PASEO_ELECTRON_FLAGS`; with
`XDG_SESSION_TYPE` unset the `Paseo Debug` window was `IsViewable` and the
root mean was 0.06 after 115 s.
