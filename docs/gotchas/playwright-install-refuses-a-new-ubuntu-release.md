# `playwright install chromium` fails on a distro release Playwright does not know

**Playwright 1.58 stops with `does not support chromium on ubuntu26.04-x64` on
Ubuntu 26.04, yet the Ubuntu 24.04 build it would download runs fine there.**

Set `PLAYWRIGHT_HOST_PLATFORM_OVERRIDE=ubuntu24.04-x64` for the install only.
Launching the installed browser needs no override. The dev shell's
`paseo-playwright-install` helper retries with the override when it sees this
error, so the browser still comes from the checkout's pinned Playwright.

Drop the override once the repo's Playwright knows the host release.

**Confirmed:** 2026-11-14, Paseo `origin/main` (Playwright 1.58.2, Chromium
revision 1208) on Ubuntu 26.04: plain install failed with the error above, the
override installed `chromium-1208`, and a headless launch without the override
reported Chromium 145.0.7632.6.
