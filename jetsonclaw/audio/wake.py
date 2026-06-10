"""Wake word detection via openWakeWord.

Critical Jetson lesson: feed int16 numpy arrays, NEVER float32 — float32 input
produces near-zero scores on clear speech while int16 scores 0.99+.
"""

from __future__ import annotations

import numpy as np


class WakeDetector:
    def __init__(self, model: str, framework: str, threshold: float) -> None:
        from openwakeword.model import Model as WakeModel  # heavy import, defer

        self._model_name = model
        self._threshold = threshold
        self._model = WakeModel(wakeword_models=[model], inference_framework=framework)

    def detect(self, chunk_i16: np.ndarray) -> float | None:
        """Feed one chunk; return the score if it crossed the threshold."""
        self._model.predict(chunk_i16)
        scores = self._model.prediction_buffer[self._model_name]
        if len(scores) > 0 and scores[-1] > self._threshold:
            score = float(scores[-1])
            self._model.reset()
            return score
        return None
