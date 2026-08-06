# yt-dlp/yt-dlp — DEPEND

The maintained youtube-dl fork with a serious TikTok extractor suite: single
videos, user pages, collections (paginated via TikTok's web
`api/collection/item_list` endpoint), sounds, tags, live. Pure Python, arm64
fine, installable via pip, drivable as a subprocess or via its Python API.
For the "index 6 years of favorited TikToks" demo the realistic pipeline is:
TikTok "Download your data" JSON export gives the favorites/likes URL list
(favorites are private; no scraper sees them anonymously), then yt-dlp
resolves each URL to metadata (title, uploader, music, duration) with
`--skip-download --dump-json`, optionally with `--cookies` from the logged-in
browser profile when TikTok throws challenges.

- **Stars/health:** 182.7k, active (2026-08) · **License:** Unlicense (public domain)

## Does better than REMY
REMY has no media/metadata extraction at all. yt-dlp gives per-URL TikTok
metadata without a browser for most public videos, cookie-jar support for the
rest, and rate-limit/retry machinery a runtime-synthesized skill would never
get right.

## Read these files
- `yt-dlp/yt-dlp@5d6b8c8:yt_dlp/extractor/tiktok.py:L1293-1344` —
  `TikTokCollectionIE`: paginates `www.tiktok.com/api/collection/item_list/`
  by cursor; the pattern for enumerating any TikTok list endpoint
- `yt-dlp/yt-dlp@5d6b8c8:yt_dlp/extractor/tiktok.py:L998-1000` —
  `TikTokUserIE` incl. `tiktokuser:sec_uid` scheme for profile enumeration
- `yt-dlp/yt-dlp@5d6b8c8:yt_dlp/extractor/tiktok.py:L1483-1485` — "Fresh
  cookies (not necessarily logged in) are needed" fallback: expect
  cookie-passing to be part of any robust TikTok flow

## Lift
- Skill recipe: parse export JSON ("Activity/Favorite Videos" +
  "Activity/Like List", each item = date + link) -> `yt_dlp.YoutubeDL
  ({"skip_download": True})` per URL -> SQLite/JSON index -> voice queries.
- `--cookies-from-browser chromium` against the playwright-mcp profile when
  challenges appear.

## Avoid
- Downloading video files on the 8GB Jetson unless asked; metadata-only.
- Treating it as a favorites *discovery* tool: it cannot list a private
  favorites page anonymously; the export (or an authenticated playwright-mcp
  crawl of tiktok.com/@me favorites tab) supplies the URL list.

## License constraint
Unlicense (public domain). Cleanest possible for MIT REMY.

## Jetson cost
Pip package ~15MB, no native deps required. **ESTIMATE** ~60-100MB RSS while
extracting; a few hundred ms to a few s per URL, so a 6-year index (say 3-8k
favorites) is an hours-long background batch — run it niced, resumable.

## Effort
**S** — pip dependency + a ~100-line indexer skill.
