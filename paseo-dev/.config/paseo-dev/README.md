# paseo-dev

A personal Nix flake with the toolchain for developing Paseo. It lives outside
the Paseo repo and changes nothing in it. Stow links this directory to
`~/.config/paseo-dev`.

## First-time setup of a checkout

Run from the Paseo checkout or worktree root:

```sh
bash ~/.config/paseo-dev/scripts/paseo-dev-activate.sh   # .envrc + direnv allow
direnv exec . paseo-install             # npm ci, patches, app-deps and server builds
direnv exec . paseo-playwright-install  # Chromium for the locked Playwright
direnv exec . paseo-dev-check           # warn-only prerequisite and drift report
```

`paseo-install` runs `npm ci --ignore-scripts`, then the patch step with
`node_modules/.bin` on PATH, then `npm run build:app-deps` and
`npm run build:server`. Never install with plain `npm ci --ignore-scripts`: it
skips `patches/` and the app crashes. Scripts stay disabled so no git hook is
installed.

The activation script writes an untracked `.envrc` and excludes it through the
repo's local exclude file. The `.envrc` unsets `PASEO_HOME`, so a value leaking
from the host shell cannot point the dev stack at the real daemon's state; it
uses the checkout-local `.dev/paseo-home`.

## Optional: Electron binary for paseo-desktop-capture

`--ignore-scripts` skips Electron's binary download. Fetch it once per
checkout, then capture:

```sh
direnv exec . node node_modules/electron/install.js
direnv exec . paseo-desktop-capture
```

## Screenshot of the real desktop app

`paseo-desktop-capture` drives Paseo's capture harness. To see the full app
(`npm run dev:desktop`: Metro plus Electron) on a virtual display, run from
the checkout root:

```sh
direnv exec . paseo-desktop-shot
```

It writes `/tmp/paseo-desktop-shot.png` (`PASEO_DESKTOP_SHOT_OUT` changes it),
prints the mean pixel value (0 is black) and stops the stack afterwards. The
first run in a checkout waits for Metro's first web bundle, which takes
minutes; later runs take about two. Set `EXPO_PORT` and `PASEO_LISTEN` to run
beside another dev stack. Why it must unset `XDG_SESSION_TYPE`: see
[the gotcha](../../../docs/gotchas/electron-desktop-stays-black-under-xvfb-on-a-wayland-session.md).

## Android

`nix develop path:$HOME/.config/paseo-dev#android` adds the SDK, JDK, Gradle and
the emulator. It is only evaluated when asked for.

`paseo-emulator start` creates the AVD if missing (x86_64 `google_apis` image
at the pinned platform), boots it headless with software rendering and returns
once Android reports the boot finished. `paseo-emulator stop` ends it;
`status` says whether it runs. It needs access to `/dev/kvm` (the `kvm`
group). The AVD and adb keys live under `$XDG_DATA_HOME/paseo-dev/android`, the
pid and log under `$XDG_STATE_HOME/paseo-dev`, never in a checkout.

```sh
nix develop path:$HOME/.config/paseo-dev#android
paseo-emulator start
adb devices
paseo-emulator stop
```

Start it from an interactive shell or `direnv exec`, not as a piped one-shot
`nix develop -c paseo-emulator start | ...`: that pipe stays open until the
emulator exits. See
[the gotcha](../../../docs/gotchas/nix-develop-c-holds-a-pipe-open-while-a-background-process-lives.md).
Before the first Android Gradle build in a checkout, run
`npm rebuild react-native-enriched-markdown @shopify/react-native-skia` (see
[the enriched-markdown gotcha](../../../docs/gotchas/gradle-fails-on-enriched-markdown-after-install-with-scripts-disabled.md)
and [the Skia and `/tmp` gotcha](../../../docs/gotchas/gradle-fails-on-skia-and-tmpfs-quota-in-android-debug-build.md);
keep the checkout off a tmpfs `/tmp`). A debug APK is
`npx cross-env APP_VARIANT=development expo prebuild --platform android --clean --non-interactive`
then `./gradlew assembleDebug -PreactNativeArchitectures=x86_64` in
`packages/app/android`; `adb install` it and start `sh.paseo.debug`. On first
launch see [the ANR gotcha](../../../docs/gotchas/first-launch-on-the-headless-emulator-shows-a-system-ui-anr.md).
The SDK carries platform 36, build-tools 35, CMake and an NDK because Paseo's Gradle build needs them
(see [the gotcha](../../../docs/gotchas/gradle-android-build-needs-more-than-the-documented-sdk.md)).
`adb` keeps its keys in `~/.android`; only the AVD, emulator state, pid and log
move to XDG.

## Updating the pins

```sh
nix flake update --flake path:$HOME/.config/paseo-dev
git -C <dotfiles checkout> diff -- paseo-dev/.config/paseo-dev/flake.lock
```

Review the lock diff before committing. The Node and Java majors and the
Android versions are defined once at the top of `flake.nix`; the smoke script
(`paseo-dev-smoke`) reads them from the environment.

## Paseo's own worktree setup

A worktree created through Paseo runs its `npm ci` on the host, outside this
environment, so it needs a host Node. Without one, re-run `paseo-install`
inside the environment afterwards.
