# Roadmap

Ordered milestones. Each names the capability it unlocks, the acceptance test
that proves it, the files it touches, its rollback story, and its main risk.
Sizing is by reviewability, not evenness: M1-M3 are large because they are
substrate; the demo milestones are smaller because the substrate carries them.

The rule that sets the order: every capability increase ships with the
containment that makes it survivable, in the same milestone. That is why M0-M2
buy no demo - they are the floor the demos stand on.

---

## M0 - Safety rails (no new capability)

Independent cheap fixes that reduce today's risk and unblock later work.

- **Unlocks:** nothing new; removes a live GPL violation and closes leak paths.
- **Acceptance:** `pip` cannot pull GPL Piper (guard in place); an agent session
  with `permissions.deny` cannot Read `~/.remy/secrets/**`; the redaction filter
  strips a planted `gho_`/`ya29.` token from an episodic write; Spotify re-auth
  works against a `127.0.0.1` redirect. `--selftest` green.
- **Files:** requirements/pyproject + `audio/tts.py` (pin), agent session
  settings (deny glob), `brain/episodic.py` + event-bus writer (redaction),
  Spotify token/redirect config.
- **Rollback:** each fix is independent; revert the one that regresses.
- **Risk:** low. The redaction regex is the only thing that could hide real
  output - keep it narrow and tested.

## M1 - Agent SDK migration (ADR 0001)

- **Unlocks:** resume-by-session-id, mid-session input, interrupt, per-call
  `can_use_tool` gating, hook-driven progress events. Substrate for M3-M7.
- **Acceptance:** every existing agent path (self.iterate, agent.task,
  agent.solve, heartbeat) works through the SDK; a session started, then
  resumed by id after a REMY re-exec, continues the same conversation;
  `--selftest` includes an SDK smoke test and stays green.
- **Files:** `brain/claude.py` (reimplement on `ClaudeSDKClient`, keep
  `AgentLine` interface + CLI fallback behind a config flag), `config.py`
  (`claude.engine = "sdk"|"cli"`), `brain/` tests, `--doctor` (SDK present).
- **Rollback:** flip the flag to the retained CLI path (today's behavior).
- **Risk:** medium. The SDK client is bound to one async context; the brain
  layer must own the lifecycle. Benchmark session RSS on-box before deleting the
  CLI path.

## M2 - Sandbox foundation (ADR 0003)

- **Unlocks:** safe skill execution; the precondition for giving the agent Bash
  and for toolchain jobs. Closes the in-process `action.script` hole.
- **Acceptance:** a hostile test skill (`while True`, and a read of
  `~/.remy/secrets`) is contained - it times out, cannot see the secret, cannot
  block the event loop; a normal skill still runs; `--doctor` reports whether
  unprivileged user namespaces and cgroup delegation are available; `--selftest`
  green.
- **Files:** new `sandbox/profiles.py` (A/B/C), `skills/loader.py` (route all
  execution through profile A, delete in-process import/exec), skill manifest
  schema (network opt-in, resource fields), `--doctor` (userns/bwrap/cgroup
  checks), sandbox tests.
- **Rollback:** the pre-sandbox in-process path is deleted, not re-enabled;
  fallback is that a skill needing the sandbox is refused with a spoken reason,
  never run unsandboxed.
- **Risk:** high, and front-loaded on purpose. If unprivileged user namespaces
  are off on the L4T r36 kernel, the whole approach needs a kernel config change
  (fallback landrun is much weaker). This check runs on first power-on.

## M3 - Detached job engine (ADR 0002)

- **Unlocks:** demo 4. Breaks the `_route_lock` ceiling - the owner keeps
  talking while a job runs.
- **Acceptance:** "get my CS104 repo and work the assignment, tell me when it's
  done" starts a detached job; "how's it going?" reports progress mid-run;
  "stop that" cancels; the job survives a REMY self-restart and re-attaches by
  session id; completion is announced. Chat works throughout. `--selftest`
  green including a job state-machine test.
- **Files:** new `jobs/` (sqlite store, state machine), new `jobrunner.py`,
  `app.py` (`_route` long-task branch, background job watcher, new
  status/cancel intents), `router/intents.py` (job intents), `--doctor`
  (linger, `systemctl --user`), TUI/PWA jobs view, tests.
- **Rollback:** flag long tasks back to the in-process agent path inside
  `_route_lock` (today's behavior); reconcile any live units on boot.
- **Risk:** medium. Crash-recovery reconciliation must not double-run a live
  job; gate the boot sweep on unit `ActiveState`. Requires `enable-linger`.

## M4 - Credential broker (ADR 0004)

- **Unlocks:** the auth substrate for demos 1-4. GitHub first.
- **Acceptance:** GitHub device flow completes by voice (REMY speaks the code,
  owner approves on phone); the token is usable by a skill; the refresh token
  never appears in a transcript, log, git diff, or the skill's env; a missing
  credential raises a spoken grant walk-through. `--selftest` green.
- **Files:** new `secrets/` (age store, broker, grant flow), `skills/loader.py`
  (`requires.credential` -> broker URL+bearer injection, retire raw
  `requires.env` for secrets), `router/intents.py` (grant flow), onboarding docs
  (owner-provisioned Google OAuth client), `--doctor` (age present, store
  perms), tests.
- **Rollback:** `requires.credential` skills refuse without the broker;
  `requires.env` stays only for the Spotify migration window.
- **Risk:** medium. Google's headless OAuth is genuinely awkward (no device-flow
  for Calendar/Gmail, 127.0.0.1-only loopback, 7-day tokens in "Testing"); the
  phone walk-through and the owner-provisioned client must be validated on-box.

## M5 - Capability acquisition + REMY MCP (ADR 0005, 0007)

- **Unlocks:** demo 3 (email -> calendar) end to end. Runtime tool acquisition.
- **Acceptance:** "add the thing from that email to my calendar" reads Gmail,
  extracts the event, writes Calendar, and speaks confirmation, keyboard
  untouched; a new capability added by writing a registry entry between two
  spawns is usable on the second with no REMY restart; the agent can `speak`
  and `read_memory` through REMY's own MCP server. `--selftest` green.
- **Files:** new `capabilities/` (registry, schema, `--mcp-config` composer with
  `--strict-mcp-config`), new `mcp_server.py` + shared `agent_tools/`,
  `brain/claude.py` (compose mcp-config + allowlist per request),
  `skills/loader.py` (`requires.capability`), `--doctor` (node, server catalog
  health), tests.
- **Rollback:** an empty registry means the agent has exactly today's tools.
- **Risk:** medium. Depends on google_workspace_mcp OAuth working through the
  broker; keep the server catalog curated so a misheard request cannot install a
  hostile server.

## M6 - Browser and vision capture (ADR 0008, browser via ADR 0005/0006)

- **Unlocks:** demos 2 and 1.
- **Acceptance:** "show me three header variants for my portfolio, then push the
  second one" renders three variants, screenshots them to `/preview`, takes a
  spoken selection, commits, and deploys; "index my favorited TikToks and write
  up my profile" acquires the data (export JSON or authenticated crawl),
  processes it, and writes durable docs on disk; the camera `capture_frame()`
  tool yields a JPEG the agent Reads. Peak RAM stays within 8GB with qwen
  unloaded during the browser task. `--selftest` green.
- **Files:** capability registry entries (playwright-mcp), `agent_tools/`
  (v4l2 capture, headless-shell screenshot), the ADR 0006 model-unload policy,
  `--doctor` (v4l-utils, chromium-headless-shell, playwright), tests.
- **Rollback:** unregister browser/capture tools; those demos become
  unavailable, nothing else regresses.
- **Risk:** medium-high on RAM. The unload-and-run policy is load-bearing here;
  measure the browser task peak on-box before enabling by default.

## M7 - Synthesis hardening (proves demos 5 and 6)

- **Unlocks:** general capability - synthesize a novel capability at runtime,
  sandbox it, test it, install it, then perform the request.
- **Acceptance:** a novel spoken request (not any of demos 1-4) results in REMY
  acquiring the capability and performing it, keyboard untouched; a repo-planted
  "cheat" file specific to a demo causes that demo's acceptance to FAIL (proving
  nothing demo-specific is hardcoded); the two-stage gate rejects a no-op diff;
  the overseer cancels a thrashing self-edit session before it finishes.
- **Files:** `skills/selfiterate.py` (two-stage acceptance gate + last-known-good
  list, from backlog #8), self-edit overseer/watchdog (backlog #9),
  `skills/activate.py` (sandboxed activation via profile B), tests.
- **Rollback:** disable the extra gate/overseer, reverting to today's
  repair-before-rollback gate (`selfiterate.py:139-162`).
- **Risk:** medium. This is where "the owner invents a sixth demo" is really
  tested; the value is generality, so the anti-hardcoding test matters as much
  as the happy path.

---

## What this program changes in the existing backlog

**Made obsolete as separate items** (absorbed and concretized here):

- "bubblewrap sandbox for skill execution" (bigger bet) -> M2, promoted to the
  primary containment mechanism with three concrete profiles.
- "can_use_tool permission gate" (bigger bet) -> folded into M1 (the SDK
  migration) and M7 (where gating self-edit matters).

**Made newly urgent:**

- Pin MIT Piper (was backlog #5) -> M0. Reading the source confirmed
  `audio/tts.py` imports the GPL `piper1-gpl` API in-process, so this is a live
  license violation, not a hypothetical upgrade risk.
- The in-process `action.script` execution hole -> M2. Not in the old backlog;
  it is the most dangerous existing behavior (arbitrary synthesized Python in
  REMY's own process, no timeout, full state access).
- Spotify redirect-URI migration -> M0. Provider policy changed under REMY
  (localhost/LAN-IP redirects banned in 2025); the existing token flow is
  likely already broken for re-auth.

**Left in the backlog, deliberately not in this program:** the voice-loop
quality items - semantic end-of-turn (smart-turn), reconciling memory
consolidation (mem0), wake-word hardening, silero pre-clip, streaming partials,
barge-in, the qwen `<functioncall>` prompt. They improve the loop REMY already
has; this program is about the loop it does not. They can be interleaved between
milestones since they touch the STT/turn/memory paths, not the agent path.

## Where the four ceilings were wrong or imprecise

Verified against source; corrections in writing as requested:

1. **Shell - understated, not wrong.** The bash path is real (`loader.py:98`).
   The brief missed the worse hole: `action.script` and `converse()` run
   in-process (`loader.py:69-86`, `loader.py:111-120`), which is the thing M2
   most needs to fix.
2. **Job lifetime - one correction.** "Nothing survives longer than ten
   minutes" is wrong: the 600s is a per-line inactivity timeout
   (`claude.py:71-72`, `config.py:84`), not a wall-clock cap, so a working
   session already runs for hours. The real ceiling is `_route_lock` plus zero
   persistence across REMY's self-restart - which M3 addresses and the brief got
   right otherwise.
3. **Credentials - correct.** One hand-rolled integration; `mcp_config` plumbed
   and unused. Confirmed.
4. **Sight - one correction.** The agent already sees images: Read ingests
   PNG/JPG and Read is allowed (`config.py:88`). The missing half is capture,
   not ingestion, which shrinks the sight milestone (M6/ADR 0008) to two small
   wrappers rather than a vision subsystem.

## Dependencies added across the program (all process-boundary or pure-Python)

`claude-agent-sdk` (M1, pure Python), `bubblewrap` + `socat` (M2, apt), systemd
user lingering (M3, OS feature), `age` (M4, apt), node + curated MCP server
binaries (M5, on-demand), `v4l-utils` + `chrome-headless-shell` + playwright
(M6, apt/CDN). Every one is a separate process or pure Python; none is linked
into REMY's MIT codebase. Each lands with its `--doctor` check in the same
commit.

## Stop point

This is the end of Phase 1. No implementation code has been written. The owner
reviews this roadmap and picks the starting milestone (the forced order makes M0
or M1 the only sensible starts). Every RAM and latency figure in the ADRs is
marked ESTIMATE and must be measured on the powered-on Jetson before the
milestone that depends on it is enabled by default.
