# snakers4/silero-vad — DEPEND

Enterprise-grade VAD. ONNX model, **<1ms per 30ms chunk** on one CPU thread,
`onnxruntime>=1.16.1`, no GPU.

- **Stars/health:** 9.9k, active (2026-07) · **License:** MIT (vendorable/depend)

## Does better than REMY
REMY's turn detection is a raw silence threshold on amplitude. Silero gives a
real *speech-probability* per frame — the foundation for reliable barge-in
detection (is the user actually speaking over the TTS, vs speaker echo/noise)
and the VAD gate feeding a semantic turn model (smart-turn / livekit).

## Read these files
- `snakers4/silero-vad@76e3dc4:README.md` — ONNX-only usage,
  `torch.set_num_threads(1)`, <1ms/chunk, runs anywhere onnxruntime does
  (incl. arm64/Jetson).

## Lift
Depend directly on the ONNX model via onnxruntime (skip the torch.hub path). It
also ships inside whisper_trt and wyoming-faster-whisper, so you may already be
pulling it transitively.

## Avoid
The torch.hub loading path — use the raw ONNX + onnxruntime.

## License constraint
MIT — vendorable/dependable with attribution.

## Jetson cost
~2MB ONNX, <1ms/chunk CPU, negligible RAM, no GPU. This is the cheapest possible
add.

## Effort
**S.**
