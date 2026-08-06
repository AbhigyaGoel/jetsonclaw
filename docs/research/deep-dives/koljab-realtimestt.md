# KoljaB/RealtimeSTT — PORT

MIT streaming STT wrapper: real-time partial transcription via a small model
while a larger model finalizes, driven by a Silero + WebRTC VAD state machine.

- **Stars/health:** 10.0k, active (2026-06) · **License:** MIT (vendorable)

## Does better than REMY
REMY's STT is utterance-complete (~1s after silence). RealtimeSTT emits
**stabilizing partial transcripts during speech**
(`on_realtime_transcription_stabilized`), which (a) lets the UI show live text
and (b) feeds a text-EOU / barge-in decision *before* the user stops talking —
directly attacking REMY's non-streaming latency.

## Read these files
- `KoljaB/RealtimeSTT@a89fabb:RealtimeSTT/audio_recorder.py:L119-196` — the
  config surface: `realtime_model_type="tiny"`, `post_speech_silence_duration=0.2`
  (silence gate), `silero_deactivity_detection`, dual `webrtc_sensitivity`/
  `silero_sensitivity`, `on_realtime_transcription_stabilized`. The two-model
  streaming pattern and how VAD deactivity ends a turn faster than a fixed
  threshold.

## Lift
The dual-VAD + realtime-tiny-partials pattern, running a streaming pass over
REMY's arecord stream: faster-whisper `tiny` for partials, `base` for final.

## Avoid
Its PyAudio-centric device/capture layer — REMY is arecord-only; keep REMY's
capture and feed frames in.

## License constraint
MIT — vendorable with attribution.

## Jetson cost
A second `tiny` faster-whisper instance (~75MB, CPU) for partials; runs on CPU,
no GPU RAM. Measure CPU headroom with base+tiny concurrent.

## Effort
**M.**
