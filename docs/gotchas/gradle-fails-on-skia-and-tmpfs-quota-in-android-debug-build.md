# Paseo's Android debug build fails on missing Skia binaries, then on a full `/tmp`

**`./gradlew assembleDebug` stops at `Skia prebuilt binaries not found.  Run
\`npx install-skia\` to fix this` in `:shopify_react-native-skia:configureCMakeDebug`.**
The package downloads `libskia.a` in an install script, and `paseo-install`
runs with scripts disabled. Run `npm rebuild @shopify/react-native-skia` once
per checkout (needs network). Keep every ABI directory it creates: the in-repo
`paseo-diff-prototype` module builds all four ABIs whatever
`-PreactNativeArchitectures` says, and fails with `ninja: error ...
libskparagraph.a ... missing` for an ABI you deleted.

**The same build then fails with `Disk quota exceeded` in unrelated tasks
(`externalNativeBuildDebug`, `compileDebugKotlin`, `mergeExtDexDebug`) while
`df` still shows free space.** `/tmp` is a 16 GB tmpfs here, and a checkout
with `node_modules` (4 GB) plus native intermediates exceeds what is left of
it. Put the scratch checkout on the real disk (for example under
`~/.cache`), not `/tmp`. `git worktree move` cannot cross filesystems: copy
with `cp -a`, then `git worktree repair <new path>`, and re-run
`expo prebuild --clean` because the generated project embeds absolute paths.

**Confirmed:** 2026-11-14, Paseo `origin/main`: both failures reproduced as
above; on the real disk the debug build finished in about 9 minutes
(`BUILD SUCCESSFUL`, 218 MB APK).
