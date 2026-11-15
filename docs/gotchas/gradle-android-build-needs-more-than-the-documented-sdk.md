# Paseo's Android Gradle build needs an NDK, platform 36, build-tools 35 and CMake, not what `docs/android.md` lists

**`./gradlew` in `packages/app/android` stops at `Failed to install the
following SDK components: ndk;27.1.12297006` and later `platforms;android-36`
and `build-tools;36.0.0`, then `The SDK directory is not writable`.** The SDK
from Nix lives in the read-only store, so Gradle cannot fetch what is missing,
as `docs/android.md` says it will.

The Paseo docs name platform 35 and build-tools 35.0.0 and no NDK. The build
actually uses compileSdk 36, build-tools 36.0.0 and the NDK pinned by
React Native (`ndkVersion` in `node_modules/react-native/gradle/libs.versions.toml`).
The Expo module plugin also asks for build-tools 35.0.0 next to 36.0.0
(`:expo:generateDebugRFile`), and the native modules ask for CMake 3.22.1
(`:react-native-nitro-modules:configureCMakeDebug`). The flake's `android`
attribute set defines all of them in one place.
Re-check them against the `[ExpoRootProject]` lines Gradle prints when Paseo
bumps its toolchain.

**Confirmed:** 2026-11-14, Paseo `origin/main` (Expo 57, React Native from its
lock file): with platform 35 and no NDK Gradle failed as above. With platform 36
and NDK 27.1.12297006 `:app:tasks` and `:app:checkDebugAarMetadata` succeeded.

**Confirmed:** 2026-11-14, same checkout: with build-tools 35.0.0 and CMake
3.22.1 added, `./gradlew assembleDebug` reached `BUILD SUCCESSFUL` and wrote
`app-debug.apk`.
