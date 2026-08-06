# nspady/google-calendar-mcp — DEPEND (fallback only)

Focused node/TypeScript Google Calendar MCP server (npm
`@cocal/google-calendar-mcp`, stdio default). Twelve calendar tools including
free/busy and multi-account. Kept on the bench as the lighter alternative if
taylorwilsdon/google_workspace_mcp proves too heavy or flaky for
calendar-only requests; its on-disk token file also demonstrates the
pre-seeded-auth pattern. Downsides for REMY: calendar only (the Gmail-to-
Calendar demo still needs a Gmail server), and its OAuth callback is
hardcoded to localhost ports 3500-3505, which a phone on the LAN cannot
reach — auth must be pre-seeded from another machine.

- **Stars/health:** 1.2k, active but slowing (last push 2026-06) · **License:** MIT

## Does better than REMY
Clean OAuth-token lifecycle for a single Google API; free/busy queries;
multi-account handling.

## Read these files
- `nspady/google-calendar-mcp@5f301a0:src/auth/server.ts:L39-50` — port range
  `{start: 3500, end: 3505}`; redirect URI built as
  `http://localhost:${port}/oauth2callback`. Localhost-only: headless Jetson
  cannot complete this flow from a phone.
- `nspady/google-calendar-mcp@5f301a0:src/auth/server.ts:L201-255` — auth
  flow: starts loopback server, prints URL to stderr, `open(authorizeUrl)`;
  `openBrowser=false` path exists, but the redirect still lands on localhost.
- `nspady/google-calendar-mcp@5f301a0:src/auth/tokenManager.ts:L46-88` —
  tokens persisted as plain JSON at `getSecureTokenPath()` with mode 0600.
  This is the escape hatch: run auth once on a laptop, copy the token file to
  the Jetson, refresh works from there.

## Auth
Desktop-app OAuth credentials (`gcp-oauth.keys.json` via
`GOOGLE_OAUTH_CREDENTIALS` env). Google test-mode tokens expire in 7 days;
publish the OAuth app to production to avoid weekly re-auth.

## Lift
The token-file portability pattern (pre-auth elsewhere, ship the file) for any
localhost-bound OAuth server. mcp-config: `{"command": "npx", "args":
["@cocal/google-calendar-mcp"], "env": {"GOOGLE_OAUTH_CREDENTIALS": "..."}}`.

## Avoid
Making it the primary Google path — google_workspace_mcp covers calendar plus
Gmail/Drive in one process with a LAN-reachable callback.

## License constraint
MIT — dependable.

## Jetson cost
Node stdio process ~50-80MB RSS **ESTIMATE**, npx cold start ~1-2s. Pure JS,
arm64 fine.

## Effort
**S** — but only worth it if the workspace server disappoints.
