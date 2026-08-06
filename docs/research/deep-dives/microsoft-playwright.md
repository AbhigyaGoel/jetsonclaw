# microsoft/playwright — DEPEND

Browser automation with Microsoft-hosted chromium builds. The load-bearing fact
for REMY: the official CDN ships real linux-arm64 chromium and
chromium-headless-shell builds mapped to `ubuntu22.04-arm64`, so a Jetson
(JetPack r36 = Ubuntu 22.04 aarch64) gets first-class browser binaries with
`playwright install chromium` and never touches Ubuntu's snap-only chromium.
System requirements page explicitly lists "Ubuntu 22.04 / 24.04 (x86-64 or
arm64)". Python bindings (microsoft/playwright-python, 14.9k stars, Apache-2.0,
active 2026-08) wrap a bundled node driver; both node and python work on arm64.

- **Stars/health:** 94k, active (2026-08) · **License:** Apache-2.0

## Does better than REMY
REMY has no browser at all today. Playwright supplies: hermetic chromium
install (no snap, no apt pinning), headless screenshot/PDF, storage-state
persistence for authenticated sessions (TikTok login), and the browser layer
under playwright-mcp and TikTok-Api.

## Read these files
- `microsoft/playwright@3eead79:packages/playwright-core/src/server/registry/index.ts:L137-141` —
  `'ubuntu22.04-arm64': 'builds/chromium/%s/chromium-linux-arm64.zip'` (full chromium)
- `microsoft/playwright@3eead79:packages/playwright-core/src/server/registry/index.ts:L172-176` —
  same mapping for `chromium-headless-shell-linux-arm64.zip`
- `microsoft/playwright@3eead79:packages/playwright-core/src/server/registry/index.ts:L48-50` —
  CDN mirrors (`cdn.playwright.dev/dbazure/download/playwright`)
- `microsoft/playwright@3eead79:packages/playwright-core/browsers.json:L4-18` —
  current revision 1237 = Chromium 152, chromium + headless-shell both installByDefault

## Lift
- `pip install playwright && playwright install chromium-headless-shell --with-deps`
  as an on-demand capability install (a REMY skill `requires.pip` step).
- Headless-shell is enough for screenshots/scraping; skip full chromium unless
  a demo needs the full browser (extensions, headed debugging).
- `context.storage_state(path=...)` to persist a TikTok login once, reuse forever.

## Avoid
- Installing firefox/webkit (wasted disk, no benefit).
- Ubuntu's `chromium-browser` apt package: it is a transitional stub that
  installs the snap (packages.ubuntu.com/jammy/chromium-browser); snap on
  Jetson is friction REMY does not need.

## License constraint
Apache-2.0. Clean for MIT REMY as a dependency.

## Jetson cost
Verified CDN sizes (HEAD, revision 1237): chromium-linux-arm64.zip 205MB
compressed, chromium-headless-shell-linux-arm64.zip 115MB compressed.
**ESTIMATE** unpacked: ~500MB / ~270MB respectively; python wheel + node driver
~50MB. **ESTIMATE** RAM idle+1 tab: headless-shell ~100-180MB RSS, full
headless chromium ~250-400MB on a real page (community-reported figures; no
on-box benchmark yet). On-demand subprocess, so it costs nothing at rest.

## Effort
**S** — pip install + one skill wrapper.
