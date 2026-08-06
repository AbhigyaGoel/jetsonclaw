# davidteather/TikTok-Api — IGNORE (no authed routes; yt-dlp covers the rest)

Unofficial Python TikTok wrapper that spins up playwright chromium sessions to
mint the signed request params TikTok's web API requires, then calls the JSON
endpoints directly. Actively maintained and MIT, but the README is explicit:
"no support for any user-authenticated routes" — if you can't see it logged
out, this library can't fetch it. REMY's favorites demo is exactly an
authenticated-only surface, so this covers none of the hard part, and for
public metadata enrichment yt-dlp does the same job with better maintenance
and no extra dependency. Ban risk is real (TikTok rotates anti-bot; the repo's
issue tray is a history of EmptyResponse breakage), which is a bad fit for a
runtime-synthesized skill that must work on first try.

- **Stars/health:** 6.5k, active (2026-07) · **License:** MIT

## Does better than REMY
Shows the "browser mints tokens, requests go direct" hybrid pattern: cheaper
than full-page crawling, sturdier than raw HTTP.

## Read these files
- `davidteather/TikTok-Api@4993fe4:TikTokApi/tiktok.py:L11-17` — built on
  `playwright.async_api`; sessions are real chromium contexts
- `davidteather/TikTok-Api@4993fe4:TikTokApi/tiktok.py:L438-481` —
  `create_sessions(headless=True, ...)`, `suppress_resource_load_types` to
  skip images/media for speed (a good trick for any REMY crawl skill)

## Lift
- `suppress_resource_load_types` idea: block image/media/font loads in
  playwright-mcp-adjacent crawls to cut Jetson bandwidth and RAM.

## Avoid
- Adding it as a dependency: authed favorites impossible, public metadata
  duplicated by yt-dlp, breakage-prone.

## License constraint
MIT. Fine, but unused.

## Effort
n/a (not adopted).
