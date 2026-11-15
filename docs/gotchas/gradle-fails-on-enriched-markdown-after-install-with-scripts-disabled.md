# Gradle refuses `react-native-enriched-markdown` after `npm ci --ignore-scripts`

**`./gradlew` fails with `[ReactNativeEnrichedMarkdown] code highlighting is
enabled but the tree-sitter grammars are not installed`, followed by `does not
specify compileSdk`.** The package fetches its grammars in an install script,
and `paseo-install` runs with scripts disabled on purpose (no git hooks).

Run `npm rebuild react-native-enriched-markdown` in the checkout, which
runs only that package's script and needs network access. `paseo-install` does
not do it because only Android builds need it.

**Confirmed:** 2026-11-14, Paseo `origin/main`: Gradle failed with the message
above; after the rebuild `./gradlew :app:tasks` reported `BUILD SUCCESSFUL`.
