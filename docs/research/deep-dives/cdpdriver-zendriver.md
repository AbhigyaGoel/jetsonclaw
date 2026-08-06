# cdpdriver/zendriver — IGNORE (AGPL library, imported in-process)

Async Python CDP driver, the maintained fork of ultrafunkamsterdam/nodriver
(4.6k stars, AGPL-3.0, stale since 2026-05). Sells itself on being
undetectable: real Chrome over raw CDP, no webdriver fingerprints, cookie
save/load for login reuse. Technically attractive for TikTok anti-bot, but it
is a *library* you `import zendriver` — in-process linkage of AGPL-3.0 code
into MIT REMY, which the license policy forbids. There is no CLI process
boundary to hide behind without writing a bespoke wrapper daemon, at which
point playwright-mcp (Apache-2.0, already an MCP server) wins outright. Also
prefers headed Chrome for stealth; headless Jetson weakens its whole pitch.

- **Stars/health:** 1.4k, active (2026-07) · **License:** AGPL-3.0

## Does better than REMY
Anti-bot evasion beyond what playwright offers stock; cookie/profile
management ergonomics.

## Read these files
- `cdpdriver/zendriver@f0bd943:README.md:L9` — fork of nodriver (same AGPL)
- `cdpdriver/zendriver@f0bd943:README.md:L14-24` — raw-CDP undetectability
  pitch, cookie save/load, `tab.find()` text-based element lookup

## Lift
- Pattern only: if TikTok blocks playwright's stock chromium, the mitigation
  is CDP-level stealth (real Chrome binary, no automation banner, humanized
  timing) — replicate with MIT-licensed patches/flags on playwright, or fall
  back to the data-export path that needs no scraping at all.

## Avoid
- `pip install zendriver` anywhere in REMY. AGPL-3.0 in-process is
  disqualifying; nodriver upstream is the same license.

## License constraint
AGPL-3.0 — cannot vendor or import in-process into MIT REMY. A separate-process
wrapper would be legal ("DEPEND (process boundary)") but is not worth building
given playwright-mcp.

## Effort
n/a (not adopted).
