# usefulsensors/moonshine — DEPEND

A purpose-built streaming voice STT. Portable C++ core over OnnxRuntime with
Python/Swift/Java bindings. Gen-2 models add a **flexible input window (no 30s
zero-pad)** and **encoder+decoder-state caching for incremental audio** — the two
Whisper limitations that cause latency.

- **Stars/health:** 10.6k, active (2026-08) · **License:** MIT for code + English
  models; **non-English models are non-commercial** (Moonshine Community License)

## Does better than REMY
Emits incremental transcript events (`LineStarted`/`LineUpdated`/
`LineTextChanged`/`LineCompleted`) — live partials REMY can't do today. Benchmark:
Tiny Streaming 34M params, **237ms on a Raspberry Pi 5** (arm64, no GPU) at 12%
WER vs Whisper Tiny 5,863ms. Implies very low CPU latency on the Orin, leaving
the GPU entirely for qwen. Ships prebuilt **arm64 Linux** shared libs.

## Read these files
- `usefulsensors/moonshine@cc16956:README.md:L111-118` — WER/latency table
  (Pi5 arm64); `:L124-144` — why-not-Whisper + caching/streaming design.
- `python/src/moonshine_voice/transcriber.py:L27-95` — the streaming event API.
- `python/src/moonshine_voice/mic_transcriber.py` — mic→stream helper.

## Lift
English models + the Python `Transcriber` for a streaming/partials path.

## Avoid
Non-English models (non-commercial license). WER (12% tiny / 7.8% small) is
higher than Whisper base — use for partials/wake-confirm, keep Whisper/
whisper_trt for the final transcript.

## License constraint
MIT (code + English models). Non-English weights are non-commercial —
PATTERN-ONLY.

## Jetson cost
Tiny 34M / small 123M params — trivial vs Whisper; CPU-only, arm64 prebuilt.

## Effort
**M.**
