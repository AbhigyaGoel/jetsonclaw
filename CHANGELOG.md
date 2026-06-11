# Changelog

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
