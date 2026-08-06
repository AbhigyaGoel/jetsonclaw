# REMY

Recursively Evolving Machine, Yours. A voice assistant running on a Jetson Orin Nano Super. You may be running
*inside* this app via its self-iteration feature — your edits take effect after
the harness commits, tests, and restarts it. Keep changes minimal and focused.

## Hard constraints (Jetson Orin Nano, JetPack r36, Python 3.10)

- **numpy must stay <2** — tflite-runtime crashes on numpy 2.x
- **Never use PyAudio** — mic capture is `arecord` via subprocess only
- **openWakeWord needs int16 audio** — float32 silently scores ~0; do not "fix" this
- **Whisper runs CPU-only** (pip ctranslate2 has no CUDA on aarch64)
- Python 3.10 syntax only (no `tomllib` without the tomli fallback, no 3.11+ features)
- Keep files small and focused; defer heavy imports (model loads) out of module top-level

## Billing and auth (non-negotiable)

REMY authenticates to Claude via the owner's subscription through the Claude Code
CLI. `claude-agent-sdk` subprocesses that same CLI and inherits that auth; it is
not the Anthropic Messages API client and introduces no per-token billing.

- No code path, systemd unit, shell profile, or container env may set
  `ANTHROPIC_API_KEY`. `--doctor` must assert it is unset and fail loudly if not.
- The model-invocation boundary stays behind one interface. Anthropic paused a
  billing change on 2026-06-15 that would have moved `claude -p` and Agent SDK
  usage off subscription limits onto a separate monthly credit; it may return in
  some form. Swapping to API-key billing must be a config change, never a
  rearchitecture.
- Milestone zero, before any capability work: a cost ledger. Parse token usage
  from the `result` line of `stream-json`, persist per-session cost, and expose
  it via "status report" and the dashboard. Every later milestone reports its
  measured cost per run.
- Long detached jobs consume far more than today's utterances. Token and
  wall-clock budgets are enforced by the overseer, not advisory. A job that
  exceeds budget cancels and reports.
- Anything qwen2.5:3b can resolve locally never reaches Claude. Treat the tiered
  local router as a cost control, not a latency optimization.

## Architecture

- `remy/events.py` — async EventBus; every component publishes here, TUI + web UI subscribe
- `remy/audio/` — mic (arecord), wake (openWakeWord), stt (faster-whisper), tts (piper)
- `remy/router/intents.py` — pure intent parsing; this decides fast-skill vs local chat vs agent
- `remy/brain/` — ollama (local fast chat) and claude (headless Claude Code sessions)
- `remy/skills/` — spotify, selfiterate
- `remy/app.py` — the orchestrator
- `remy/__main__.py` — entry; boot guard runs before other imports, don't add imports above it
- `~/.remy/` — runtime state: SOUL.md/USER.md/MEMORY.md persona files, voices, boot counters

## Validation

`python3 -m remy --selftest` must pass — it imports every module and runs
`tests/`. Self-iteration changes that fail it are automatically discarded.
Add tests in `tests/` for any new pure logic (especially intent parsing).
