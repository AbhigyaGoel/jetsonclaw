# anthropic-experimental/sandbox-runtime — DEPEND (for agent Bash) + PATTERN-ONLY (proxy design)

Anthropic's own sandbox for Claude Code (`srt <command>`, npm
`@anthropic-ai/sandbox-runtime`). On Linux it is bubblewrap underneath, plus a
proxy-based network filter and a small seccomp helper. This is exactly the
"industry answer" for agent shell on Linux: bwrap for fs/net namespaces,
domain filtering pushed to a host-side HTTP/SOCKS proxy because
`--unshare-net` is all-or-nothing. Claude Code >= late 2025 ships this as the
built-in `/sandbox` Bash sandbox (Linux deps: bubblewrap + socat; optional
seccomp filter), so REMY's headless `claude -p` sessions can get profile-C
containment by turning it on rather than building it.

- **Stars/health:** 4.9k, active (2026-08) · **License:** Apache-2.0

## Does better than REMY
REMY has no plan for network egress control at all. srt: sandbox gets NO
network namespace; socat bridges Unix sockets into the sandbox where listeners
on :3128/:1080 forward to host proxies that enforce a domain allowlist. Also:
credential masking (bind sentinel files over real credential paths), mandatory
deny of dangerous files (found via ripgrep pre-scan), symlink-escape
hardening.

## Read these files
- `anthropic-experimental/sandbox-runtime@97c197f:src/sandbox/linux-sandbox-utils.ts:L1635-1682` —
  the two-stage design: outer bwrap (`--unshare-net`, `--unshare-pid`,
  `--proc`, binds), inner `apply-seccomp` (nested user+PID ns, PR_SET_NO_NEW_PRIVS,
  seccomp blocking `socket(AF_UNIX)`); prebuilt apply-seccomp binaries for x64
  AND arm64.
- `anthropic-experimental/sandbox-runtime@97c197f:src/sandbox/linux-sandbox-utils.ts:L576-600` —
  the socat Unix-socket network bridge and the honest LIMITATION note: on
  Linux, domain filtering happens at the host proxy, not the kernel boundary.
- `anthropic-experimental/sandbox-runtime@97c197f:src/sandbox/linux-sandbox-utils.ts:L1747` —
  baseline argv is `['--new-session', '--die-with-parent']`; REMY's profiles
  should start from the same pair.

## Lift
- For agent sessions (profile C): enable Claude Code's built-in sandbox
  (settings: `sandbox`, `allowUnsandboxedCommands`; docs
  https://code.claude.com/docs/en/sandboxing) instead of wrapping claude in
  REMY's own bwrap. Deps on jammy arm64: `apt install bubblewrap socat`.
- For REMY's own runner: copy the argv-order discipline (deny binds emitted
  after allow binds, resolve symlinks before masking, `--ro-bind /dev/null
  <file>` and `--tmpfs <dir>` as deny primitives, mask store dir ro-bound
  last).
- If skills later need domain-scoped network, run `srt` as the wrapper for
  those skills rather than reimplementing the proxy stack in Python.

## Avoid
Vendoring the TS into REMY's Python; running the proxy stack for every 2-second
skill invocation (proxy spin-up cost dwarfs the skill; profile A is
net-on/net-off, which is enough for v1). Beta-quality: pin the npm version.

## License constraint
Apache-2.0. Fine to depend on; NOTICE if ported.

## Effort
**S** to enable for Claude Code sessions; **M** if srt wraps skill runs too.
