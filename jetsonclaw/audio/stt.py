"""Speech-to-text via faster-whisper.

`base` model on CPU/int8: pip ctranslate2 has no CUDA on aarch64, and `tiny`
mishears uncommon words. base/int8 is the accuracy/latency sweet spot on Orin.
"""

from __future__ import annotations

import numpy as np


class Transcriber:
    def __init__(self, model: str, device: str, compute_type: str,
                 beam_size: int, language: str) -> None:
        from faster_whisper import WhisperModel  # heavy import, defer

        self._beam_size = beam_size
        self._language = language
        self._model = WhisperModel(model, device=device, compute_type=compute_type)

    def transcribe(self, audio_f32: np.ndarray) -> str:
        segments, _ = self._model.transcribe(
            audio_f32, beam_size=self._beam_size, language=self._language
        )
        return " ".join(s.text.strip() for s in segments).strip()
