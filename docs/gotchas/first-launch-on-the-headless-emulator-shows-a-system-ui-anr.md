# The first launch on the software-rendered emulator shows "System UI isn't responding"

**A screenshot taken right after launching the app shows an ANR dialog over
it.** The headless emulator renders in software with no snapshot, so the first
heavy launch starves System UI. The app itself is fine: tap `Wait` (`adb shell
input tap` on the button) and capture again after a few seconds.

**Confirmed:** 2026-11-14: Paseo debug build (`sh.paseo.debug`) launched into
the Expo dev launcher; the dialog appeared on the first capture and was gone
after `Wait`.
