"""Microphone capture via arecord subprocess.

PyAudio is deliberately NOT used: on Jetson its device indices are unstable,
break after backgrounding, and fail with channel errors. arecord reading raw
PCM from ALSA directly has been rock solid.
"""

from __future__ import annotations

import subprocess

import numpy as np


class Microphone:
    def __init__(self, device: str, sample_rate: int, chunk_samples: int) -> None:
        self._device = device
        self._rate = sample_rate
        self._chunk_bytes = chunk_samples * 2  # S16_LE
        self._proc: subprocess.Popen | None = None

    def open(self) -> None:
        self.close()
        self._proc = subprocess.Popen(
            [
                "arecord", "-D", self._device, "-f", "S16_LE",
                "-r", str(self._rate), "-c", "1", "-t", "raw", "-q",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,  # ALSA confmisc/dmix warnings are cosmetic
        )

    def read_chunk(self) -> np.ndarray | None:
        """Blocking read of one chunk as int16. None when the stream dies."""
        if self._proc is None or self._proc.stdout is None:
            return None
        data = self._proc.stdout.read(self._chunk_bytes)
        if data is None or len(data) < self._chunk_bytes:
            return None
        return np.frombuffer(data, dtype=np.int16)

    def reopen(self) -> None:
        self.open()

    def close(self) -> None:
        if self._proc is not None:
            self._proc.kill()
            self._proc.wait()
            self._proc = None

    @property
    def alive(self) -> bool:
        return self._proc is not None and self._proc.poll() is None


def rms(chunk: np.ndarray) -> float:
    if chunk.size == 0:
        return 0.0
    return float(np.sqrt(np.mean(chunk.astype(np.float32) ** 2)))
