# Changelog

## Unreleased — Billing/auth guardrails + cost ledger

- cost ledger (`remy/cost.py`): parses `total_cost_usd`/`usage`/`session_id` from
  the agent `result` line (both engines) and persists one row per session to
  `~/.remy/cost.jsonl`; surfaced in the spoken/dashboard status report. Measures
  real agent spend on the subscription (free to record) instead of guessing.
- `--doctor` now asserts `ANTHROPIC_API_KEY` is unset — a core check that fails
  loudly, because a set key silently switches Claude Code to pay-as-you-go
  billing instead of the subscription.
- CLAUDE.md gains a non-negotiable "Billing and auth" section; README/design docs
  corrected to reflect subscription-backed billing (the 2026-06-15 separate-credit
  change was paused, may return; the model-invocation boundary stays swappable).

## Unreleased — Capability Program M3 (detached job engine, core)

- new `remy/jobs/`: the sqlite job table + state machine + crash-recovery sweep
  that ADR 0002 hand-rolls because no queue library stores the agent-session link
- state machine queued -> running -> {done,failed,cancelled} with paused
  reachable from running; illegal transitions are rejected at the store
- reconciliation is pid/unit-gated: a `running` row whose systemd unit is gone is
  flipped to failed, but a live unit is never touched (no double-run), with the
  unit-liveness check injected so it's testable without systemd
- the job row carries the Claude session id so a job re-attaches via the M1
  `resume=` path after a REMY self-restart
- NOT YET (on-box gated): `jobrunner.py`, the `systemd-run --user` launch, the
  app.py long-task branch, and the TUI/PWA jobs view — they need systemd user
  lingering and build on the unvalidated M1 SDK

## Unreleased — Capability Program M2 (sandbox foundation)

- new `remy/sandbox/`: bubblewrap profile argv builder (three frozen profiles —
  skill / pip / toolchain, each wrapped in `systemd-run --user --scope` for
  memory/pids/wall-clock caps) and host-viability detection (unprivileged
  userns, bwrap, cgroup v2 memory delegation)
- `--doctor` now reports the three sandbox prerequisites; the userns check is the
  single biggest on-box unknown and gates the whole approach
- `docs/design/on-box-checklist.md`: the runbook for the powered-on Jetson
  (M0 audio validation, M1 SDK benchmark/resume, M2 userns probe)
- NOT YET (on-box gated): routing skill execution through the sandbox and
  deleting the in-process `exec_module` path in loader.py — that behavior switch
  needs a real bwrap + a passing userns check to validate

## Unreleased — Capability Program M1 (Agent SDK, scaffolding)

- second agent engine behind the existing `AgentLine` interface: `[claude]
  engine = "sdk"` drives `claude-agent-sdk`'s `ClaudeSDKClient` (resume-by-id,
  mid-session input, per-call gating); `engine = "cli"` (default) is unchanged
- session id is surfaced as an `AgentLine(kind="session")` so a future job runner
  can persist it and resume after a restart; both engines gained a `resume=<id>`
  path (CLI `--resume`, SDK `resume=`)
- the M0 deny-list settings file is reused by the SDK engine (`settings=`)
- `--doctor` gates on the SDK only when it's the selected engine; `--selftest`
  covers option/message mapping without requiring the package installed
- new optional extra `.[sdk]`; not a hard dependency
- ON-BOX GATE (not yet done): benchmark SDK session RSS + cold-start vs the CLI,
  and verify `resume=<id>` re-attaches across a REMY restart, before the CLI
  fallback is removed

## Unreleased — Capability Program M0 (safety rails)

- Piper runs out-of-process: REMY execs the `piper` binary and streams its audio
  instead of importing the (now GPL-3.0) `piper-tts`; a license guard fails
  `--selftest`/`--doctor` if a GPL piper-tts is installed in-process
- agent Read is denied on REMY's secret stores via a managed `--settings` file
  (`~/.remy/secrets`, tokens, credentials) — enforced before those stores exist
- secret-shaped tokens are redacted before any durable write (episodic memory,
  daily summaries, the evolution journal)
- `scripts/spotify_auth.py`: link Spotify over a 127.0.0.1 loopback redirect
  (Spotify rejects `localhost`/LAN-IP redirects since 2025)

## v0.3.0 - 2026-06-12

- provider-agnostic chat brain: ollama or any OpenAI-compatible endpoint
- watch skills: scheduled, speak only on changed output
- episodic memory: every interaction logged, keyword recall, idle-time consolidation into daily summaries and long-term facts
- remember/recall voice commands, status report
- configurable identity (name the assistant whatever you want)
- custom wake word model support and training guide
- phone voice input and TTS on the dashboard PWA
- doctor command, ruff lint gate in CI

## v0.2.0 - 2026-06-11

- conversation memory, streaming TTS (sentence by sentence)
- hot-loaded SKILL.md skills with pip dependency activation and quarantine
- typed input on every surface (TUI, dashboard, stdin)
- spoken confirmation gate before agent tasks; no shell access for the agent by default
- first voice-commanded self-modification verified on hardware

## v0.1.0 - 2026-06-10

- wake word, whisper STT, Piper TTS, intent router
- dual brains: local qwen via ollama, headless Claude Code for agent tasks
- self-iteration with selftest gate, last-known-good, crash-loop auto-revert
- Spotify, TUI, web dashboard, systemd service, installer
