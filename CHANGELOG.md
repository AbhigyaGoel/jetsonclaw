# Changelog

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
