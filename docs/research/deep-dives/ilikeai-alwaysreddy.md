# ILikeAI/AlwaysReddy — VENDOR (lift files)

Hotkey-triggered talking-LLM with pluggable transcription/TTS/LLM managers and a
bundled `piper_tts/` — the closest structural sibling to REMY (Piper + a manager
pattern).

- **Stars/health:** 757, **archived** (last push 2025-03) · **License:** MIT
  (vendorable — lift files, don't depend on the repo)

## Does better than REMY
Clean separation of `transcription_manager.py` / `tts_manager.py` /
`completion_manager.py` with a `config_default.py` + `config_loader.py` override
pattern, and a `TTS_apis/` that shows how to sentence-stream Piper — the same
TTS REMY uses. A tidy template for REMY's TTS module boundaries, and a reference
for making Piper output cleanly cancellable (a prerequisite for barge-in).

## Read these files
- `ILikeAI/AlwaysReddy@aa77c82:tts_manager.py` + `piper_tts/` — Piper
  sentence-streaming wrapper.
- `config_default.py` + `config_loader.py` — layered-config pattern matching
  REMY's coding-style rules.

## Lift
The MIT Piper streaming manager and the manager-decomposition, directly.

## Avoid
Depending on it (archived). Windows-hotkey `input_apis/` are irrelevant — REMY
is wake-word driven.

## License constraint
MIT — vendor with attribution.

## Effort
**S.**
