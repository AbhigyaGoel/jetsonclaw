# Migration Path

The constraint: `main` is never left unbootable, and `python3 -m remy
--selftest` passes at every commit (the self-mod gate depends on it). REMY may
be modifying itself while this work lands, so each step is independently
shippable and independently revertable.

## Principles

- One milestone per branch; commits small enough to bisect.
- Every new subsystem lands behind a config flag defaulting to today's
  behavior, so a half-built subsystem cannot change the running system until it
  is switched on.
- New external dependencies are added to `--doctor` in the same commit, so a
  missing `bwrap`, `age`, node, or broken MCP server is diagnosable by voice.
- Every new failure mode gets an `ERROR` event and a spoken form (the owner is
  often not at a screen).
- `docs/` and `EVOLUTION.md` update in the same commit as the behavior change.

## Order and why

The order is forced by two rules: containment before the capability it contains,
and substrate before the things built on it.

1. **Safety rails that are cheap and independent** (M0). Pin MIT piper (a live
   GPL violation today), add the `permissions.deny` secrets glob and the
   redaction filter, migrate the Spotify redirect URI. None of these depend on
   anything; all reduce current risk. They can land in any order among
   themselves.

2. **Agent SDK migration** (M1) before everything, because the job engine, the
   permission gate, and REMY-as-MCP all build on the SDK. Landing it first
   behind a flag, with the CLI path retained, means a bad SDK build reverts to
   exactly today's behavior.

3. **Sandbox** (M2) before Bash, before jobs, before capability acquisition,
   because it is the containment those need. Killing in-process script execution
   also closes the worst current hole on its own, so M2 has standalone value
   even if later milestones slip.

4. **Job engine** (M3) after M1 (needs the SDK runner) and M2 (needs profile C).
   This is where the `_route_lock` ceiling breaks.

5. **Credential broker** (M4) after M2 (secrets live behind the sandbox
   boundary) and before capability acquisition (which needs provider auth).

6. **Capability acquisition + REMY MCP** (M5) after M1/M4. This is the first
   milestone that unlocks a demo end to end (demo 3).

7. **Browser + vision capture** (M6) after M5 (browser is an MCP server in the
   registry) and ADR 0006's unload policy. Unlocks demos 1 and 2.

8. **Synthesis hardening** (M7) last, because it exercises everything below it:
   the solve-then-absorb loop now has shell, credentials, jobs, and browser, and
   needs the two-stage gate and overseer to synthesize safely. Proves demo 5 and
   the unannounced demo 6.

## Rollback per milestone

Every milestone reverts to the milestone below it, not to a broken partial
state, because each is flag-gated:

- M1: config flag back to the CLI brain path.
- M2: skills that require the sandbox are refused (not run unsandboxed); the
  old in-process path is deleted, not re-enabled, so the fallback is "fewer
  skills run," never "the hole reopens."
- M3: long tasks fall back to the in-process agent path inside `_route_lock`
  (today's behavior); jobs already running are reconciled on boot.
- M4: `requires.credential` skills refuse without the broker; `requires.env`
  keeps working for the Spotify migration window only.
- M5: an empty capability registry means the agent has exactly today's tools.
- M6: no browser/capture tools registered means those demos are unavailable; the
  rest is unaffected.
- M7: the extra gate/overseer can be disabled, reverting to today's
  repair-before-rollback self-mod gate (`selfiterate.py:139-162`).

## The on-box gate

Several milestones carry on-box verification that cannot be done while the
Jetson is off (unprivileged user namespaces, cgroup delegation, OAuth loopback
from the phone, RAM under a browser task). Those checks are written into
`--doctor` and `--selftest` as they land, so the first power-on runs them
automatically and refuses to enable a subsystem whose kernel/OS prerequisite is
missing. The design assumes the userns check (ADR 0003) is the one most likely
to fail; landrun is the documented fallback if it does.
