# dscripka/openWakeWord — DEPEND (in use; turn on the levers)

REMY's current wake engine. 80ms frames, a shared Google speech-embedding
backbone + small per-word classifiers; int16 audio input (matches REMY).

- **Stars/health:** 2.6k, active (2025-12) · **License:** Apache-2.0

## Tuning REMY is probably missing
From `dscripka/openWakeWord@368c037:README.md`:
- **`vad_threshold`** (`:L107`) — a bundled Silero VAD gate so a wake only fires
  when VAD simultaneously exceeds threshold; "significantly reduce false-positive
  activations in the presence of non-speech noise."
- **`enable_speex_noise_suppression=True`** (`:L105`) — Speex NS, explicitly
  **supported on arm64 Linux**; reduces both false-reject and false-accept in
  constant noise.
- **custom verifier models** (`:L115`) — a second-stage per-voice filter for
  high-FP deployments.
- default threshold `0.5` is a starting point; tune per environment. Target is
  **<0.5 false-accepts/hr, <5% false-reject** (`:L123,146`).

## Critical custom-training gotcha (issue #335, open)
Following the documented `augment_clips` recipe for a *custom* wake word yielded
**~177 FP/hr vs 0.09 FP/hr clean** — background-noise mixing on positive clips
collapses positive↔negative separability (Fisher 13.3→6.1). If REMY trains a
custom "Remy" word: do **not** blindly apply the full augmentation recipe to
positives; validate FP/hr on a held-out negative set, or use a pre-trained model.

## Read these files
- `@368c037:README.md:L105-115` (vad_threshold, Speex arm64, verifier),
  `:L146,162-180` (FA/FR eval: DiPCo corpus for FA, 5-10dB SNR + RIR for FR).
- Issue #335 — the custom-training FP root-cause analysis.

## Lift
Already vendored — turn on the levers above and adopt the FA/FR eval method.

## License constraint
Apache-2.0.

## Jetson cost
`libspeexdsp` + speexdsp-ns wheel (arm64-supported), negligible RAM.

## Effort
**S.**
