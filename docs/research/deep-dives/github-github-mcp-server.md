# github/github-mcp-server — DEPEND

GitHub's official MCP server, written in Go. Three consumption modes: hosted
remote HTTP server at `https://api.githubcopilot.com/mcp/`, local Docker image,
or a single static binary — and GitHub ships prebuilt `Linux_arm64` release
tarballs, so the Jetson runs it natively with zero runtime deps. Covers repos,
issues, PRs, actions, code security; exactly what the "work a GitHub classroom
repo for 30 minutes" demo needs. Local binary supports PAT auth or an OAuth
login with a device-code fallback for headless boxes.

- **Stars/health:** 32k, active (2026-08) · **License:** MIT

## Does better than REMY
Everything GitHub: full toolset registry with `--toolsets` filtering,
`--read-only` mode, lockdown mode, tool aliasing. Battle-tested by every MCP
host.

## Read these files
- `github/github-mcp-server@3778a41:README.md:L218-222` — `claude mcp add github
  -e GITHUB_PERSONAL_ACCESS_TOKEN=$GITHUB_PAT -- docker run -i --rm ...`; PAT
  via env var is the whole auth story for the simple path.
- `github/github-mcp-server@3778a41:README.md:L405-413` — no-Docker path:
  `go build` (or grab release binary), config is
  `{"command": "/path/to/github-mcp-server", "args": ["stdio"]}`.
- `github/github-mcp-server@3778a41:README.md:L312` — pointer to
  `docs/oauth-login.md`: native-binary OAuth uses PKCE loopback, and when no
  browser is available falls back to GitHub's **device-code flow** ("Visit
  https://github.com/login/device and enter the code WDJB-MJHT") — REMY can
  speak the code aloud and the owner authorizes from their phone. Tokens are
  in-memory only in that mode.
- `github/github-mcp-server@3778a41:README.md:L1571-1576` — `--read-only` flag
  for a safe first-contact toolset.

## Auth
Simplest: fine-grained PAT in `GITHUB_PERSONAL_ACCESS_TOKEN` (persistent,
scopeable, no browser ever). Fancier: device-code OAuth, ideal for
voice-driven acquisition but tokens do not persist across restarts. For REMY,
store a PAT once in config and pass via env in the mcp-config entry.

## Lift
Release binary `github-mcp-server_Linux_arm64.tar.gz` (v1.8.0) dropped into
`~/.remy/mcp/bin/`; an mcp-config entry with `stdio` + PAT env. The device-code
UX pattern (speak code, wait for poll success) is worth copying for other OAuth
acquisitions.

## Avoid
The Docker route on Jetson (image is multi-arch but Docker adds RAM/complexity
for no gain over the static binary). The hosted remote HTTP server requires
OAuth wiring per host; PAT header works but the local binary is simpler and
offline-testable.

## License constraint
MIT — process-boundary dependency, no issue.

## Jetson cost
Static Go binary, spawned per `claude -p` session, ~25-50MB RSS **ESTIMATE**,
sub-second startup. Zero resident cost between sessions.

## Effort
**S** — download binary, write mcp-config entry, mint PAT.
