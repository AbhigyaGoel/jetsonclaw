# rclone/rclone — PATTERN-ONLY (the headless OAuth relay)

The canonical answer to "complete a Google OAuth loopback flow on a box with no
browser." rclone runs the loopback listener on 127.0.0.1:53682 wherever the
browser is: either (a) `rclone authorize <backend>` on the owner's laptop,
which does the full flow locally and prints a base64 token blob the user pastes
back to the headless machine, or (b) SSH `-L 53682:localhost:53682` so the
headless listener appears local to the laptop. Google's loopback redirect never
has to leave the machine running the browser, which is the only thing Google
allows (device flow excludes Calendar/Gmail scopes; LAN-IP redirects are not
registerable for native clients).

- **Stars/health:** 59k, active (2026-08) · **License:** MIT

## Does better than REMY
REMY's Spotify auth was hand-rolled once; rclone has a general "authorize any
OAuth backend from a second machine" state machine that decouples where the
browser runs from where the token lands, with version-mismatch checks on the
pasted blob.

## Read these files
- `rclone/rclone@5629f26:cmd/authorize/authorize.go:L27-52` — the standalone
  `rclone authorize <backend> [b64blob | id secret]` command run on the
  browser machine.
- `rclone/rclone@5629f26:fs/config/authorize.go:L11-69` — builds a temp
  remote, runs the normal OAuth config flow in "authorize" mode, emits the
  paste-back blob.
- `rclone/rclone@5629f26:lib/oauthutil/oauthutil.go:L50-56` — fixed
  `127.0.0.1:53682` bind + redirect URL (loopback only, never LAN IP).
- `rclone/rclone@5629f26:lib/oauthutil/oauthutil.go:L726-748` — headless side:
  prints the exact `rclone authorize ...` command to run elsewhere, then
  blocks on a `config_token` prompt; decode failure handled (L748).
- `rclone/rclone@5629f26:lib/oauthutil/oauthutil.go:L950-993` — the local
  auth webserver + browser-open on the machine that has one.

## Lift
Port the relay shape, not the code: REMY's credential broker generates the
auth URL with `redirect_uri=http://127.0.0.1:<port>` and either (a) speaks a
short instruction while pushing the URL to the phone dashboard, with a tiny
"paste result" endpoint, or (b) serves the callback catcher itself when the
browser is a laptop SSH-forwarded to the Jetson. Also copy the "temp remote,
suppress confirm, output blob" separation so any provider plugs in.

## Avoid
Vendoring Go; the OOB `urn:ietf:wg:oauth:2.0:oob` path still present in the
code (L44-47) is dead — Google removed OOB support.

## License constraint
MIT — pattern or port both fine.

## Effort
S — the pattern is ~150 lines of Python in the broker.
