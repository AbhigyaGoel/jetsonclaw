# FiloSottile/age — DEPEND (at-rest encryption, eyes open about the key)

Small, modern file encryption (X25519 or scrypt passphrase, ChaCha20-Poly1305).
The right tool if REMY encrypts its secrets store at rest. The honest caveat:
on an unattended headless Jetson the age identity key must itself live on the
same disk (no TPM; OP-TEE/fTPM exists on Orin under JetPack 6.1+ but needs
EKB/fuse provisioning — impractical for a hobby device, and without burned
fuses the hardware key is a public test key). So age here buys tamper-evidence
and protection of *backups/SD-card-theft*, not protection from a process that
can read the identity file. That is still worth having; it is not a substitute
for the broker.

- **Stars/health:** 23k, stable/slow (2026-03) · **License:** BSD-3-Clause

## Does better than REMY
REMY's `~/spotify_tokens.json` is plaintext with unknown mode bits. age gives
a vetted primitive with a one-file CLI (`age`/`age-keygen`), arm64 packages in
Ubuntu, and a Go/Rust ecosystem (str4d/rage, Apache-2.0, if Rust is preferred).

## Read these files
- `FiloSottile/age@706dfc1:scrypt.go:L39-77` — scrypt recipient, workFactor
  2^18 (~1s), ChaCha20-Poly1305 wrap; this is the passphrase mode.
- `FiloSottile/age@706dfc1:scrypt.go:L123-193` — scrypt identity/decrypt side.
- `FiloSottile/age@706dfc1:cmd/age/age.go` — CLI wiring; subprocess use model.

## Lift
`~/.remy/secrets/` as age-encrypted per-credential files
(`google-calendar.age`), identity at `~/.remy/secrets/.identity` chmod 0600,
decrypt only inside the broker process, plaintext never on disk. Passphrase
mode is a non-option for unattended boot (nobody to type it), so use X25519
identity file and accept the local-disk threat model explicitly in docs.

## Avoid
Pretending the identity file changes the threat model for on-box processes;
gnome-keyring/SecretService instead (needs dbus session + unlock — the
classic headless trap, and `keyrings.alt` plaintext fallback is worse than an
0600 file while looking safer); systemd-creds (needs systemd >= 250; JetPack 6
Ubuntu 22.04 ships 249 — unavailable, and host-key mode is the same
key-on-disk model anyway).

## License constraint
BSD-3-Clause — subprocess or library, both fine with MIT.

## Effort
S — apt install age; ~50 lines in the broker.
