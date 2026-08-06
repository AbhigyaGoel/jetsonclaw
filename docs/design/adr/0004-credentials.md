# ADR 0004: age-encrypted secret store plus a token broker

Status: accepted — core landed 2026-08-06 (M4: store, broker, env-scrub,
--doctor); real OAuth refreshers, the age round-trip, loader broker-injection,
and the Spotify migration are on-box gated
Date: 2026-08-06

## Context

REMY has one integration and one secret: Spotify, a hand-rolled token JSON at
`~/spotify_tokens.json` (`config.py:99-100`). The skill mechanism can declare
`requires.env` (`loader.py:168-169`), which puts raw secrets into a skill's
environment.

The demos need distinct third-party auth (Google, GitHub, more), acquired at
runtime in response to a spoken request, by an owner with a phone but no
keyboard. And the thing handling those secrets is a self-modifying agent that
commits its own code (`selfiterate.py:188-191`) and logs everything to episodic
memory - so the primary adversary is not another local user, it is REMY's own
synthesized skills and agent sessions leaking secrets into prompts, transcripts,
logs, or git.

Research (`docs/research/deep-dives/`: 99designs-aws-vault, filosottile-age,
rclone-rclone, cli-cli) established the reality:

- Google device flow cannot grant Calendar or Gmail scopes; those need a
  browser-completed loopback flow, and loopback redirects must be 127.0.0.1
  (LAN IPs are not registerable for native clients). An OAuth client left in
  "Testing" status issues 7-day refresh tokens.
- GitHub device flow works fully, with a speakable code; or depend on `gh`.
- Spotify banned `localhost` and LAN-IP redirect URIs in 2025, so REMY's
  current flow likely needs migration regardless.
- keyring/SecretService is a headless dbus-and-unlock trap; systemd-creds needs
  systemd 250 (Jetson has 249); the Orin fTPM needs fused secure boot to mean
  anything (impractical).

## Decision

Store secrets encrypted at rest and hand skills short-lived tokens through a
broker, never the refresh secret.

- Store: `~/.remy/secrets/` (0700, outside the git tree), one age-encrypted
  file per credential, an age X25519 identity file at 0600. The broker process
  is the only decryptor.
- Broker: a small in-REMY component (not a separate daemon unless it must be).
  A skill manifest declares `requires.credential: <provider>`. At spawn the
  broker injects `REMY_CRED_URL=http://127.0.0.1:<random-port>` plus a
  per-invocation random bearer token; the skill fetches a fresh ~1-hour access
  token on demand; the refresh token stays in the broker. This is aws-vault's
  credential-server shape.
- Grant flow: a missing credential raises a grant-needed event that drives the
  voice-plus-phone walk-through (open this URL on your phone, approve, read me
  the code / it lands on the dashboard), then stores the result and retries.
  GitHub device flow is the first provider supported - it is the cheapest proof
  of the whole loop, purely by voice.
- Leak prevention, layered, all available today:
  - Claude Code `permissions.deny: ["Read(~/.remy/secrets/**)", "Read(./.env*)"]`
    (deny beats allow), set on every agent session.
  - Env-scrub before spawning any agent session: strip `SPOTIFY_*`, `GH_TOKEN`,
    provider secrets from the child env.
  - A redaction filter on episodic-memory and event-bus writes (regex for
    `ya29.`, `gho_`, `refresh_token`, `AIza`), since REMY self-commits and logs.
  - Per-invocation bearer tokens, so a leaked transcript is already stale.

## Rationale

- The store is chosen for the real adversary (REMY's own agents), and age adds
  at-rest protection for the secondary disk-theft case without a keyring daemon.
- The broker makes leakage structurally hard: a skill that is fully compromised
  still only holds a 1-hour access token and a per-run bearer, never the refresh
  token or the encryption key.
- Every rejected store fails this specific box (dbus, systemd version, TPM
  fuses); age plus a broker is the honest fit.

## Alternatives rejected

- `requires.env` with raw secrets (today's mechanism). Rejected: puts refresh
  tokens into skill environments and, by extension, one prompt away from a
  transcript.
- keyring/SecretService, systemd-creds, sops, TPM. Rejected per the version and
  headless constraints above; sops also solves secrets-in-git, which REMY bans.
- A full secrets manager (Vault, Infisical). Rejected: server + database is
  absurd for one Jetson, and Vault is BUSL.

## Consequences

- New dep: `age` (or `rage`) binary, apt/arm64. A `remy/secrets/` module for
  the store and broker.
- The skill manifest schema gains `requires.credential`; the loader wires the
  broker env at spawn instead of raw env.
- Onboarding gains a documented, owner-run step: create your own Google Cloud
  OAuth client and set it to "In production (unverified)", or Gmail/Calendar
  refresh tokens die every 7 days. This is a docs artifact, not code REMY can
  ship.
- Spotify migration: move `~/spotify_tokens.json` into the broker and fix the
  redirect URI as migration #1.

## Verify on-box

- age encrypt/decrypt round-trip and identity-file permissions under the remy
  user.
- The loopback grant flow completing from the owner's phone against a
  127.0.0.1 redirect (the phone's browser hits its own loopback - confirm the
  chosen relay actually delivers the code to REMY).
- Claude Code honors the `permissions.deny` Read glob for `~/.remy/secrets/**`.
