# 99designs/aws-vault — PATTERN-ONLY (the credential broker shape)

The cleanest prior art for "master credential stays with the broker, child
process only ever sees short-lived material." aws-vault keeps long-lived AWS
keys in an encrypted backend (OS keyring, or an encrypted file backend with
`AWS_VAULT_FILE_PASSPHRASE` for headless), then `aws-vault exec profile -- cmd`
spawns the child with either (a) short-lived STS creds in env, or (b) better:
a localhost HTTP credential server and only a URL + random bearer token in
env (`AWS_CONTAINER_CREDENTIALS_FULL_URI` / `AWS_CONTAINER_AUTHORIZATION_TOKEN`).
The child fetches fresh creds on demand; the refresh secret never enters the
child's environment, argv, or logs.

- **Stars/health:** 9.0k, maintenance mode (2025-12) · **License:** MIT

## Does better than REMY
REMY's `requires.env` injects the actual secret into the skill process, where
any `print(os.environ)` or crash log leaks it. aws-vault's ECS-server mode
injects only a capability pointer; secrets are pulled per-request, cached
broker-side, and scoped by a per-session random token over 127.0.0.1.

## Read these files
- `99designs/aws-vault@74e2f7a:cli/exec.go:L239-243` — scrub long-lived
  `AWS_ACCESS_KEY_ID`/`AWS_SESSION_TOKEN` from the child env before spawn.
- `99designs/aws-vault@74e2f7a:cli/exec.go:L263-277` — start broker server,
  set only `AWS_CONTAINER_CREDENTIALS_FULL_URI` + auth token in child env.
- `99designs/aws-vault@74e2f7a:server/ecsserver.go:L69-96` — bind
  `127.0.0.1:0` (random port), generate random bearer token, wrap all routes
  in `withAuthorizationCheck`.
- `99designs/aws-vault@74e2f7a:server/ecsserver.go:L29-32` — constant-shape
  bearer check returning 403.

## Lift
REMY broker port: refresh tokens live only in the broker process. A skill's
manifest says `requires.credential: google-calendar`; at spawn REMY sets
`REMY_CRED_URL=http://127.0.0.1:<port>/cred/google-calendar` +
`REMY_CRED_TOKEN=<random>`; a 5-line helper in the skill SDK fetches an
access token (Google access tokens live 1h — refresh stays home). Bearer
token is per-skill-invocation, so a leaked transcript containing it is dead
after the session. Also copy the env-scrub step for `claude -p` subprocesses.

## Avoid
Porting the AWS-specific STS logic; depending on the repo itself (maintenance
mode, AWS-only). chamber (MIT) is the same idea but requires AWS SSM —
irrelevant. Infisical/Vault are servers with their own auth — far too heavy
for one Jetson.

## License constraint
MIT — pattern or port both fine.

## Effort
M — broker HTTP server + per-provider refresh logic + skill SDK helper.
