# cli/cli (gh) — DEPEND (GitHub creds solved; do not rebuild)

GitHub's official CLI. `gh auth login` runs the OAuth device flow (user visits
github.com/login/device on the phone, types an 8-char code — zero
redirect-URI problems, fully headless-friendly), stores the token in the OS
keyring when one exists and falls back to plaintext `~/.config/gh/hosts.yml`
when not (the headless-Jetson case). `gh auth token` hands the token to any
other process, so synthesized skills never need their own GitHub OAuth app.

- **Stars/health:** 46k, active (2026-08) · **License:** MIT

## Does better than REMY
Complete device-flow implementation (via github.com/cli/oauth), scope
management, multi-account, token refresh-on-expiry for GitHub Apps, and a
sanctioned token hand-off (`gh auth token`) that other tools (git credential
helper included) already consume.

## Read these files
- `cli/cli@8b72a8e:internal/authflow/flow.go:L27-47` — `oauth.Flow` with
  minimum scopes `repo, read:org, gist`; `DetectFlow()` (L95) auto-picks
  device flow when no browser.
- `cli/cli@8b72a8e:internal/config/config.go:L246-256` — token lookup order:
  keyring first, plaintext hosts.yml fallback.
- `cli/cli@8b72a8e:internal/config/config.go:L297-314` — `TokenFromKeyring`
  via zalando/go-keyring.
- `cli/cli@8b72a8e:internal/keyring/keyring.go:L22-60` — 60s-timeout wrapper
  because SecretService hangs on headless boxes (exactly the dbus pain REMY
  would hit).
- `cli/cli@8b72a8e:pkg/cmd/auth/token/token.go:L31-46` — `gh auth token`
  prints the active token for consumption by other tools.

## Lift
For any GitHub capability a synthesized skill wants: broker runs
`gh auth status`; if absent, `gh auth login --device` (device code is
speakable: "go to github.com slash login slash device and type WDJB dash
MJHT"). Skill gets `GH_TOKEN=$(gh auth token)` injected at spawn, or just
calls `gh` directly. Note gh on headless Ubuntu stores plaintext in
hosts.yml — chmod 600 by gh already; consistent with REMY's 0600 threat
model. Fine-grained PAT pasted into the phone dashboard is the boring
fallback for repo-scoped least privilege.

## Avoid
Building a GitHub OAuth app for REMY; shipping gh's client secret pattern to
other providers (GitHub tolerates embedded client secrets, Google does not
for restricted scopes).

## License constraint
MIT — depend via subprocess, no issue.

## Effort
S — apt/binary install exists for arm64; broker glue only.
