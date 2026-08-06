# rhasspy/wyoming — VENDOR

A tiny, well-specified peer-to-peer protocol: newline-delimited JSON events
(`Event{type, data, payload}`) over a socket, with an explicit pipeline-stage
enum and per-stage event types (`Detect`, `Transcript`, `Synthesize`,
`AudioChunk/Start/Stop`).

- **Stars/health:** 383, active (2026-07) · **License:** MIT (vendorable)

## Does better than REMY
Gives a clean, transport-agnostic contract between wake/stt/tts/intent stages.
REMY's stages are in-process; adopting Wyoming's `Event` envelope + stage enum
lets REMY (a) define a stable internal event schema, and (b) later split STT/TTS
onto a second box without rewriting the core — a real answer to the 8GB ceiling.

## Read these files
- `rhasspy/wyoming@bf65f4e:wyoming/event.py:L20-95` — the whole protocol:
  `Event` dataclass, `Eventable` ABC, `async_read_event`/`async_write_event`
  JSONL framing with `data_length`/`payload_length` headers. ~100 lines.
- `rhasspy/wyoming@bf65f4e:wyoming/pipeline.py:L1-50` —
  `PipelineStage{WAKE, ASR, INTENT, HANDLE, TTS}` and `RunPipeline{start_stage,
  end_stage, wake_word_name, restart_on_end, announce_text}` for start/end-stage
  control (STT-only, or TTS-only announcements).

## Lift
The `Event` envelope and `PipelineStage` enum, close to verbatim, as REMY's
inter-stage message format.

## Avoid
Nothing major; it's minimal by design.

## License constraint
MIT — vendorable with attribution.

## Jetson cost
Pure-Python, zero native deps, negligible RAM/latency.

## Effort
**S.**
