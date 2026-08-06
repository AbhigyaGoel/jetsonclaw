# microsoft/playwright-mcp — DEPEND (primary browser path)

Browser-as-MCP-server. This is the shortest path to giving REMY's headless
`claude -p` session a browser: REMY already plumbs `--mcp-config`, and
playwright-mcp exposes navigate/click/type/screenshot plus an accessibility
*snapshot* tool that lets the model act on structured text instead of pixels,
so no vision round-trips are needed for most flows. The npm package
`@playwright/mcp` (v0.0.79) is now a thin CLI shim: the actual tool code lives
in the playwright monorepo (`packages/playwright-core/src/tools/mcp`) and the
package depends on a playwright alpha, which means arm64 support is inherited
directly from playwright's ubuntu22.04-arm64 chromium builds.

- **Stars/health:** 35.8k, active (2026-08) · **License:** Apache-2.0

## Does better than REMY
REMY's agent has WebFetch only (static HTML, no JS, no auth). playwright-mcp
adds: real rendered pages, login flows with persistent profile or
`--storage-state`, tab management, form filling, screenshots, network
inspection. Accessibility snapshots keep token cost low vs computer-use-style
screenshot loops.

## Read these files
- `microsoft/playwright-mcp@4c50776:cli.js:L20-27` — the whole server is
  `tools.decorateMCPCommand()` from `playwright-core/lib/coreBundle`; real
  source is in the playwright monorepo
- `microsoft/playwright-mcp@4c50776:src/README.md:L1-3` — pointer to
  `packages/playwright-core/src/tools/mcp` in microsoft/playwright
- `microsoft/playwright-mcp@4c50776:README.md:L428-447` — flags: `--headless`,
  `--isolated`, `--storage-state`, `--port` (HTTP/SSE transport), env-var forms
- `microsoft/playwright-mcp@4c50776:README.md:L869-1119` — tool surface:
  browser_navigate, browser_click, browser_fill_form, browser_evaluate,
  browser_snapshot, browser_take_screenshot, browser_tabs
- `microsoft/playwright-mcp@4c50776:README.md:L805` — Docker mode is
  headless-chromium-only (same constraint REMY has anyway)

## Lift
- REMY mcp-config entry:
  `{"command": "npx", "args": ["@playwright/mcp@latest", "--headless", "--browser", "chromium"]}`.
  stdio transport, spawned per session, dies with the session.
- `--storage-state ~/.remy/browser/tiktok.json` for the authenticated TikTok
  crawl; `--isolated` for throwaway scraping.
- `browser_take_screenshot` covers the portfolio-render demo without any
  bespoke renderer.
- Caps are opt-in (`--caps=vision,pdf`) — leave off to keep the tool list small
  in the Claude context.

## Avoid
- Vision mode (`--caps=vision`) as default: coordinate clicking burns image
  tokens; snapshot mode is the point.
- Running it resident. Headed default: pass `--headless` explicitly or it will
  fail on the displayless Jetson.
- Multiple concurrent sessions sharing one persistent profile (README warns:
  one browser per profile; use `--isolated` for parallel clients).

## License constraint
Apache-2.0. Clean.

## Jetson cost
Requires node >= 18 (REMY already needs node for Claude Code CLI).
**ESTIMATE**: node MCP process ~60-100MB RSS + headless chromium ~250-400MB
while a page is open; zero at rest (on-demand spawn). Install: npm package is
tiny; the chromium download (205MB compressed, see microsoft-playwright.md)
happens once via `npx playwright-mcp install-browser` or `playwright install`.

## Effort
**S** — one mcp-config entry + one-time browser install + a storage-state
bootstrap script for TikTok login.
