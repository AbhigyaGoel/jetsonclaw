#!/usr/bin/env python3
"""Verify a wake word model offline: synthesize the phrase with Piper, feed it
through the detector, and check scores. No microphone needed.

  python3 scripts/verify_wake.py hey_jarvis_v0.1 "hey jarvis"
  python3 scripts/verify_wake.py ~/.jetsonclaw/wake/hey_remy.onnx "hey remy" --framework onnx

Exit 0 when the phrase scores above threshold and the negatives stay below it.
"""

from __future__ import annotations

import argparse
import sys

import numpy as np

NEGATIVES = ["hello there my friend", "hey jeremy how are you",
             "what a remarkable memory", "playing some music now"]
RATE = 16000
CHUNK = 1280


def synthesize_16k(text: str, voice_path: str) -> np.ndarray:
    """Piper synthesis resampled to 16kHz int16."""
    from piper import PiperVoice

    voice = PiperVoice.load(voice_path)
    chunks = list(voice.synthesize(text))
    audio = np.frombuffer(b"".join(c.audio_int16_bytes for c in chunks), dtype=np.int16)
    src_rate = chunks[0].sample_rate if chunks else 22050
    if src_rate != RATE:
        target_len = int(len(audio) * RATE / src_rate)
        audio = np.interp(
            np.linspace(0, len(audio) - 1, target_len),
            np.arange(len(audio)), audio.astype(np.float32),
        ).astype(np.int16)
    # half a second of leading/trailing silence so the model sees onset/offset
    pad = np.zeros(RATE // 2, dtype=np.int16)
    return np.concatenate([pad, audio, pad])


def max_score(detector, audio: np.ndarray) -> float:
    best = 0.0
    for start in range(0, len(audio) - CHUNK, CHUNK):
        detector._model.predict(audio[start:start + CHUNK])
        scores = detector._model.prediction_buffer[detector._model_name]
        if len(scores):
            best = max(best, float(scores[-1]))
    detector._model.reset()
    return best


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("model", help="bundled name or path to .tflite/.onnx")
    parser.add_argument("phrase", help='e.g. "hey remy"')
    parser.add_argument("--framework", default="tflite", choices=["tflite", "onnx"])
    parser.add_argument("--threshold", type=float, default=0.3)
    parser.add_argument("--voice", default=None, help="piper .onnx voice path")
    args = parser.parse_args()

    from jetsonclaw.audio.wake import WakeDetector
    from jetsonclaw.config import load_config

    cfg = load_config()
    voice = args.voice or str(
        __import__("pathlib").Path(cfg.tts.voices_dir).expanduser()
        / f"{cfg.tts.voice}.onnx")

    detector = WakeDetector(args.model, args.framework, args.threshold)

    positive = max_score(detector, synthesize_16k(args.phrase, voice))
    print(f'  "{args.phrase}": {positive:.3f}  '
          f'{"PASS" if positive > args.threshold else "FAIL"} '
          f"(threshold {args.threshold})")

    ok = positive > args.threshold
    for neg in NEGATIVES:
        score = max_score(detector, synthesize_16k(neg, voice))
        false_fire = score > args.threshold
        ok = ok and not false_fire
        print(f'  "{neg}": {score:.3f}  {"FALSE-FIRE" if false_fire else "ok"}')

    print("\nverdict:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
