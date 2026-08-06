# taylorwilsdon/google_workspace_mcp — DEPEND

The best-maintained community Google Workspace MCP server: one Python 3.10+
process covering Gmail (15 tools), Calendar (7), Drive (16), Docs, Sheets,
Slides, Forms, Tasks, Contacts, Chat — 120+ tools behind `--tools`/`--tool-tier`
filters. Runs stdio (launch via `uvx workspace-mcp`) or streamable HTTP. This
single server covers both the "read Gmail, extract event, add to Calendar"
demo and Drive access. Critically for the headless Jetson: the OAuth callback
server binds a configurable base URI, so the redirect can point at the
Jetson's LAN IP and the owner completes consent from their phone.

- **Stars/health:** 3.0k, active (2026-08) · **License:** MIT

## Does better than REMY
Whole Google surface in one process instead of three node servers; encrypted
disk-backed token cache with refresh; scope management per enabled service;
tool tiers (core/extended/complete) to keep context small.

## Read these files
- `taylorwilsdon/google_workspace_mcp@db62129:auth/oauth_config.py:L65-70` —
  `base_uri = os.getenv("WORKSPACE_MCP_BASE_URI", "http://localhost")`, joined
  with port into the callback base. Set `WORKSPACE_MCP_BASE_URI=http://<jetson-lan-ip>`
  and the phone-on-LAN consent flow works.
- `taylorwilsdon/google_workspace_mcp@db62129:auth/oauth_config.py:L246-253` —
  `GOOGLE_OAUTH_REDIRECT_URI` env overrides the redirect URI outright.
- `taylorwilsdon/google_workspace_mcp@db62129:auth/oauth_callback_server.py:L43-47` —
  minimal callback server, default port 8000, started on demand only in stdio
  mode; L147-187 shows careful port-ownership probing so a foreign listener on
  8000 is not mistaken for the OAuth server.
- `taylorwilsdon/google_workspace_mcp@db62129:auth/oauth_config.py:L237` —
  transport mode defaults to stdio.

## Auth
OAuth 2.0 confidential client: `GOOGLE_OAUTH_CLIENT_ID` +
`GOOGLE_OAUTH_CLIENT_SECRET` (one-time GCP console setup, add owner as test
user). First tool call triggers an auth URL; REMY must surface that URL to the
phone (QR on PWA, or speak a short link). Redirect URI must be registered in
GCP as `http://<jetson-ip>:8000/oauth2callback`. Google test-mode refresh
tokens expire after 7 days unless the OAuth app is set to production. Also
supports OAuth 2.1/PKCE multi-user and service-account domain delegation
(irrelevant for a personal account).

## Lift
mcp-config entry: `{"command": "uvx", "args": ["workspace-mcp", "--tools",
"gmail", "calendar", "drive", "--tool-tier", "core"], "env": {...}}`. The
LAN-redirect OAuth pattern generalizes to any synthesized capability needing
Google auth.

## Avoid
Enabling all 120+ tools (context bloat in the Claude session — use
`--tools gmail calendar drive`). Running it resident; spawn per session.

## License constraint
MIT — process-boundary dependency, no issue.

## Jetson cost
Python + FastAPI + google-api-client via uvx: ~120-200MB RSS while running
**ESTIMATE**; first `uvx` run downloads the wheel set (cache it). Startup
~2-4s **ESTIMATE** — fine for on-demand spawn, respects the no-resident rule.

## Effort
**M** — GCP OAuth client setup + redirect registration + phone consent flow is
the bulk; the mcp-config wiring itself is trivial.
