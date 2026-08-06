# livekit/agents — PORT

Apache-2.0 voice-agent framework. Its `turn-detector` plugin is a complementary
approach to smart-turn: instead of audio, it runs a **quantized text LLM (q8
ONNX) over the last ~6 chat turns / 128 tokens** to predict end-of-turn
probability from the *transcript*.

- **Stars/health:** 12.7k, active (2026-08) · **License:** Apache-2.0
  (portable)

## Does better than REMY
Text-based EOU uses REMY's already-produced STT transcript (a free signal) to
judge grammatical/semantic completeness — catches "set a timer for..."
(incomplete) vs "...five minutes" (complete) that audio-only VAD can't.

## Read these files
- `livekit/agents@5626d53:livekit-plugins/livekit-plugins-turn-detector/livekit/plugins/turn_detector/base.py:L120-180` — `run()`:
  tokenize formatted chat context, `ort.InferenceSession(...,
  providers=["CPUExecutionProvider"])`, read `eou_probability =
  outputs[0].flatten()[-1]`. Pure CPU, threads capped at 4.
- `:L60-95` — `_format_chat_ctx`: merges adjacent same-role turns, strips the
  trailing EOU token.
- `.../turn_detector/models.py:L1-9` — model `livekit/turn-detector`,
  `model_q8.onnx`, English `v1.2.2-en`.

## Lift
The text-EOU inference wrapper (`run` + `_format_chat_ctx`). Pairs with REMY's
transcript.

## Avoid
LiveKit's WebRTC job/room runtime — heavyweight, irrelevant to a single-box
Jetson.

## License constraint
Apache-2.0 — portable with attribution.

## Jetson cost
q8 ONNX small transformer on CPU; competes for CPU with faster-whisper but not
GPU RAM. Verify the exact size before adopting — **smart-turn's 8MB audio model
is the lighter option**; pick one, not both.

## Effort
**M.**
