# rhasspy/wyoming-faster-whisper — PORT

A Wyoming server wrapping **faster-whisper** (the exact STT REMY uses) on CPU,
with a silero-VAD pre-clip step.

- **Stars/health:** 360, active (2026-07) · **License:** MIT (vendorable)

## Does better than REMY
Two concrete wins:
1. Explicit CPU knobs REMY should confirm it sets: `device="cpu"`, `compute_type`
   (`int8` on aarch64), `cpu_threads=4`, `beam_size`.
2. Pre-clips audio to the speech region with silero VAD **before** Whisper to
   "reduce hallucinations on silence" — directly relevant to REMY's
   utterance-complete CPU Whisper, which hallucinates on trailing silence.

## Read these files
- `rhasspy/wyoming-faster-whisper@5b5854f:wyoming_faster_whisper/faster_whisper_handler.py:L14-57` —
  `FasterWhisperTranscriber.__init__(device="cpu", compute_type="default",
  cpu_threads=4, ...)` and `transcribe(beam_size=5, vad_filter=...,
  vad_parameters=...)`. The correct CPU config + optional built-in `vad_filter`.
- `wyoming_faster_whisper/vad.py:L1-75` — `clip_to_speech`/`clip_wav_to_speech`
  using `pysilero_vad.SileroVoiceActivityDetector` (`threshold=0.5`, `pad_ms`).
  A drop-in anti-hallucination clip.

## Lift
The silero-clip function and the CPU config values.

## Avoid
The Wyoming server wrapper if REMY stays in-process — just take the transcriber
+ vad.

## License constraint
MIT — vendorable with attribution.

## Jetson cost
`pysilero-vad` (~1.8MB ONNX + onnxruntime, few-ms CPU, tens of MB RAM) — or zero
new deps via faster-whisper's built-in `vad_filter=True` (also silero).

## Effort
**S.**
