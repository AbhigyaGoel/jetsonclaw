# home-assistant/core (assist_pipeline) — PATTERN-ONLY

The most battle-tested full-stack voice orchestrator. One `PipelineRun` drives
wake→stt→intent→tts, emitting fine-grained events to a callback; VAD sensitivity
is a first-class, user-tunable setting.

- **Stars/health:** 89.8k, active (2026-08) · **License:** Apache-2.0 (but woven
  into HA internals — pattern, not a wholesale lift)

## Does better than REMY
- Its `PipelineEventType` enum is the gold-standard event taxonomy REMY's
  EventBus/TUI should mirror — note `STT_VAD_START`/`STT_VAD_END` (the UI knows
  exactly when speech began/ended) and `INTENT_PROGRESS` (stream partial
  intent/LLM output to the UI). REMY's PWA/TUI would feel far more responsive.
- `start_stage`/`end_stage` on `PipelineRun` lets one code path serve wake-word
  runs, push-to-talk, and TTS-only announcements.
- `VadSensitivity` maps RELAXED/DEFAULT/AGGRESSIVE to seconds-of-silence — clean
  UX for tuning end-of-utterance.

## Read these files
- `home-assistant/core@6605963:homeassistant/components/assist_pipeline/pipeline.py:L385-412` — `PipelineEventType`
  (RUN/WAKE_WORD/STT/STT_VAD/INTENT/INTENT_PROGRESS/TTS/ERROR start-end pairs) +
  the frozen `PipelineEvent`.
- `:L477-695` — `PipelineStage` enum, `PipelineRun{start_stage,end_stage,
  event_callback}`, stage-order validation.
- `.../assist_pipeline/vad.py:L13-73` — `VadSensitivity.to_seconds()` +
  `VoiceCommandSegmenter` ring-buffer end-of-command detection.

## Lift
The event-type vocabulary and the start/end-stage concept (pattern port).

## Avoid
Vendoring — it's woven into HA's `hass` object, entity registry, and config-flow;
not liftable wholesale.

## License constraint
Apache-2.0 (pattern port, not a copy).

## Effort
**M** — port the event taxonomy + stage control; ignore HA plumbing.
