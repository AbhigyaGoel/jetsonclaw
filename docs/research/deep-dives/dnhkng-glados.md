# dnhkng/GlaDOS — VENDOR

A full local voice assistant with ASR/TTS/LLM abstraction, VAD, wake word, a
TUI, and a genuinely production-grade **barge-in** loop. Threaded with
`threading.Event` coordination — compatible with REMY's EventBus + Textual TUI.

- **Stars/health:** 5.7k, active (2026-08) · **License:** MIT (vendorable) —
  cleanest match in the voice-app cluster

## Does better than REMY
True barge-in. REMY's non-streaming Whisper makes its loop turn-locked; GlaDOS
interrupts TTS mid-sentence the instant VAD fires, using a pre-activation ring
buffer so the interrupting words aren't clipped. Also a Levenshtein-tolerant
wake match that survives ASR misrecognitions.

## Read these files
- `dnhkng/GlaDOS@8f19b74:src/glados/core/speech_listener.py:L40-44` — the whole
  turn-taking recipe in four constants: `VAD_SIZE=32ms`, `BUFFER_SIZE=800ms`
  pre-roll, `PAUSE_LIMIT=640ms` end-of-turn, `SIMILARITY_THRESHOLD=2`.
- `:L184-204` — `_manage_pre_activation_buffer`: on VAD confidence while
  speaking, calls `audio_io.stop_speaking()`, seeds `_samples` from the pre-roll
  deque, fires `on_interrupt("user_interrupt")`. The exact barge-in mechanism.
- `:L206-221` — `_process_activated_audio`: gap-counter end-of-turn
  (`_gap_counter >= PAUSE_LIMIT // VAD_SIZE`), cheaper than a transformer.
- `src/glados/core/audio_state.py:L15-41` — lock-guarded RMS+VAD snapshot;
  immutable `AudioSnapshot` dataclass (matches REMY's immutability rule).
- `speech_listener.py:L227-244` — `_wakeword_detected`: Levenshtein over
  transcribed tokens (a text-level fallback to openWakeWord).

## Lift
Port the `SpeechListener` state machine + pre-activation deque + gap-counter
turn detection + `AudioState`. Pure numpy/threading. Wire `on_interrupt` and
`stop_speaking()` into REMY's Piper sentence-streamer.

## Avoid
Their concrete ASR/TTS classes (their own ONNX models) — REMY keeps
faster-whisper + Piper. Don't pull `vision/`, `mcp/`, `autonomy/`.

## License constraint
MIT — vendorable with attribution.

## Effort
**M** — barge-in requires REMY's TTS to be cancellable mid-stream; the listener
port itself is S.
