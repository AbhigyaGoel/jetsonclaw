# ADR 0003: bubblewrap as the one sandbox, three profiles

Status: proposed
Date: 2026-08-06

## Context

Two holes exist today and a third is planned:

1. Skill `action.command` runs via `subprocess.run(["bash","-c",cmd])`
   (`loader.py:95-109`) with a trimmed PATH (cosmetic), 30s timeout, no
   sandbox: full filesystem and network as the remy user.
2. Worse, `action.script` handler.py and `converse()` are imported and executed
   in REMY's own process (`loader.py:111-120`, `loader.py:69-86`): no timeout,
   no isolation, full access to REMY's state, and a `while True` in a
   synthesized skill blocks the event loop.
3. The program adds Bash to agent sessions and 30-plus-minute toolchain jobs
   (git, pip, compilers, node), which need real but not crippling containment.

Research (`docs/research/deep-dives/`: containers-bubblewrap,
anthropic-experimental-sandbox-runtime, zouuup-landrun, google-nsjail,
zopefoundation-restrictedpython) converged: bubblewrap is packaged for jammy
arm64 (`bubblewrap 0.6.1`), needs no daemon, and does unprivileged-user-
namespace isolation per invocation. Everything heavier fails this box: nsjail is
unpackaged and a build fight, firejail's SUID binary is a net attack-surface
increase, gVisor and every microVM need KVM that stock L4T kernels do not
enable, podman pays GB-images and seconds of cold-start per skill call.

## Decision

One primary mechanism: bubblewrap, invoked through a single
`remy/sandbox/profiles.py` with three frozen profiles, each wrapped in a
`systemd-run --user --scope` for memory/pids/wall-clock caps.

- Profile A (run a skill, Python or shell): tmpfs root, `--unshare-all` by
  default (opt-in network per skill manifest), only the skill dir bound
  writable, `MemoryMax=512M RuntimeMaxSec=30`. The boundary is that `~/.remy`,
  secrets, and the repo do not exist inside the tmpfs root - not the PATH.
- Profile B (pip into a dedicated venv): same skeleton, network on, writes only
  the venv, `PIP_CACHE_DIR` in tmpfs, `MemoryMax=1G RuntimeMaxSec=600`.
- Profile C (toolchain job): a `systemd-run --user` transient unit (the ADR
  0002 job unit) with `PrivateUsers=yes ProtectHome=tmpfs BindPaths=<job dir>`,
  `MemoryMax=3G RuntimeMaxSec=<wall>`. Exact command lines live in the
  bubblewrap deep-dive.

Agent Bash inside profile-C units runs under Claude Code's own sandbox
(`anthropic-experimental/sandbox-runtime`: bwrap + socat + a domain-filtering
proxy, arm64 supported), which gives per-domain network egress control that raw
bwrap cannot express (`--unshare-net` is all-or-nothing).

In-process `action.script` execution is removed. Script skills run as a
subprocess under profile A. If per-call import latency hurts, adopt OVOS's
persistent one-skill-per-process worker pattern (`ovos-skill-launcher`).

Self-modification jobs stay sandboxed - not to prevent self-modification but to
bound blast radius: the agent works in a disposable git worktree with `~/.remy`
hidden by `ProtectHome=tmpfs`; commit, selftest, and restart gating stay with
the trusted harness outside the sandbox, so a bad job can at worst dirty a
throwaway worktree.

## Rationale

- bwrap is the only option that is both packaged for this box and light enough
  to wrap every skill call. systemd-run supplies the resource caps bwrap does
  not, and REMY wants transient units for job detachment regardless.
- Reusing Claude Code's sandbox for agent Bash means REMY does not invent egress
  filtering; it inherits a maintained implementation.
- Killing in-process script execution closes the most dangerous existing hole,
  independent of any new capability.

## Alternatives rejected

- nsjail, firejail, gVisor, minijail, podman, microVMs (E2B/microsandbox): each
  fails this hardware or adds attack surface; reasons in the deep-dives.
- RestrictedPython for in-process script skills. Rejected: it self-disclaims as
  a sandbox and does not stop event-loop-blocking accidents either.
- landrun (Landlock): kept only as a conditional bonus layer - kernel 5.15 is
  Landlock ABI v1 (filesystem rules only) and L4T may not enable the LSM at all.

## Consequences

- New dep: `bubblewrap` and `socat` apt packages (arm64, tiny). Claude Code's
  sandbox is enabled via its own settings, not vendored.
- Skill execution gains per-call sandbox setup latency (ESTIMATE 10-30ms bwrap
  + 200-500ms Python start on Orin); acceptable for skills, measured before
  committing to a worker-pool optimization.
- The skill manifest gains a network/opt-in and resource fields; the loader
  routes all execution through `profiles.py`.

## Verify on-box (single biggest risk first)

- `unshare -Ur true` as the remy user: unprivileged user namespaces on the L4T
  r36 kernel. bwrap's setuid fallback is removed at HEAD and jammy's package is
  non-setuid, so if this fails the whole plan needs a kernel config change.
  Put this in `--doctor` and `--selftest`.
- cgroup v2 with controller delegation for `MemoryMax`/`TasksMax` in `--user`
  mode; `CPUQuota` likely a no-op on systemd 249 unless a root drop-in adds
  `Delegate=cpu`.
- `apt install bubblewrap socat`, then Claude Code `/sandbox` reports its
  readiness.
