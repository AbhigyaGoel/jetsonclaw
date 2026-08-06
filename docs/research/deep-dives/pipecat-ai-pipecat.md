# pipecat-ai/pipecat — PORT

BSD-2 real-time voice pipeline framework. Directly implements REMY's three
weak spots: hybrid turn detection, VAD-gated barge-in with a word-count guard,
and a mic-side filter chain for denoise/AEC.

- **Stars/health:** 14.0k, active (2026-08) · **License:** BSD-2-Clause
  (vendorable/portable)

## Does better than REMY
- **Hybrid turn state machine** — silence is only a *gate*; then an audio EOU
  model confirms.
- **Barge-in false-positive guard** — `MinWordsUserTurnStartStrategy(min_words=3)`
  so backchannels ("yeah", "mhm") don't kill TTS; only a real >=3-word utterance
  interrupts. REMY has neither.
- Bundles an 8MB CPU ONNX EOU model that runs with no GPU footprint.

## Read these files
- `pipecat-ai/pipecat@08f7aed:src/pipecat/audio/turn/smart_turn/base_smart_turn.py:L99-151` — `append_audio(buffer,
  is_speech)`: accumulate audio, track `_silence_ms`, run the ML classifier only
  when `_silence_ms >= _stop_ms`. The silence-gate-then-semantic-confirm pattern.
- `:L184-240` — `_process_speech_segment` / `_predict_endpoint`: extract with
  `pre_speech_ms` lookback, cap at `max_duration_secs`, `prediction==1 →
  COMPLETE`.
- `examples/turn-management/turn-management-interruption-config.py:L31-86` —
  wires `SileroVADAnalyzer()` + `MinWordsUserTurnStartStrategy(min_words=3)`. The
  barge-in recipe.
- `src/pipecat/audio/filters/` — `rnnoise_filter.py` (the free/open denoise
  option; the koala/krisp/aic filters are proprietary SDKs).

## Lift
Port the `base_smart_turn.py` state machine and the min-words interruption
logic. Reuse the smart-turn ONNX wrapper (see the smart-turn deep-dive).

## Avoid
The full Frame/Pipeline/Transport runtime — REMY has its own EventBus; take the
turn/interruption algorithms only.

## License constraint
BSD-2-Clause — vendorable/portable with attribution.

## Effort
**M.**
