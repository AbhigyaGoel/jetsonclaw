"""The blocking audio loop: wake word watch -> record until silence.

Runs in a dedicated thread (arecord reads block); results are handed to the
asyncio world through the EventBus and a callback.
"""

from __future__ import annotations

import threading
from typing import Callable

import numpy as np

from ..config import AudioConfig, WakeConfig
from ..events import EventBus, EventType
from .mic import Microphone, rms
from .wake import WakeDetector


class CaptureLoop:
    """Owns the mic thread. On wake word: records an utterance, then calls
    on_utterance(audio_f32) from the audio thread."""

    def __init__(self, audio_cfg: AudioConfig, wake_cfg: WakeConfig, bus: EventBus,
                 on_utterance: Callable[[np.ndarray], None]) -> None:
        self._cfg = audio_cfg
        self._bus = bus
        self._on_utterance = on_utterance
        self._mic = Microphone(audio_cfg.mic_device, audio_cfg.sample_rate,
                               audio_cfg.chunk_samples)
        self._wake = WakeDetector(wake_cfg.model, wake_cfg.framework, wake_cfg.threshold)
        self._stop = threading.Event()
        self._paused = threading.Event()
        self._thread: threading.Thread | None = None
        self._level_decimate = 0

    def start(self) -> None:
        self._mic.open()
        self._thread = threading.Thread(target=self._run, name="audio-capture", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        self._mic.close()

    def pause(self) -> None:
        """Ignore the mic while JARVIS is speaking (avoid self-triggering)."""
        self._paused.set()

    def resume(self) -> None:
        self._paused.clear()

    # --- audio thread ---

    def _run(self) -> None:
        while not self._stop.is_set():
            chunk = self._mic.read_chunk()
            if chunk is None:
                if self._stop.is_set():
                    return
                self._bus.publish_threadsafe(
                    EventType.ERROR, message="mic unavailable, retrying in 3s")
                self._stop.wait(3.0)  # don't spin hot when the mic is unplugged
                self._mic.reopen()
                continue

            self._publish_level(chunk)
            if self._paused.is_set():
                continue

            score = self._wake.detect(chunk)
            if score is not None:
                self._bus.publish_threadsafe(EventType.WAKE, score=score)
                audio = self._record_utterance()
                if audio.size > self._cfg.sample_rate * 0.3:
                    self._on_utterance(audio)
                else:
                    self._bus.publish_threadsafe(EventType.ERROR, message="too short, ignored")

    def _record_utterance(self) -> np.ndarray:
        frames: list[np.ndarray] = []
        silent = 0
        chunks_for_silence = int(self._cfg.silence_secs * self._cfg.sample_rate
                                 / self._cfg.chunk_samples)
        max_chunks = int(self._cfg.max_record_secs * self._cfg.sample_rate
                         / self._cfg.chunk_samples)

        for _ in range(max_chunks):
            chunk = self._mic.read_chunk()
            if chunk is None:
                break
            frames.append(chunk)
            self._publish_level(chunk)
            if rms(chunk) < self._cfg.silence_rms:
                silent += 1
            else:
                silent = 0
            if silent >= chunks_for_silence:
                break

        if not frames:
            return np.array([], dtype=np.float32)
        audio = np.concatenate(frames)
        return audio.astype(np.float32) / 32768.0

    def _publish_level(self, chunk: np.ndarray) -> None:
        # Every 4th chunk (~3 updates/sec at 80ms chunks) is plenty for UIs.
        self._level_decimate = (self._level_decimate + 1) % 4
        if self._level_decimate == 0:
            self._bus.publish_threadsafe(EventType.AUDIO_LEVEL, rms=rms(chunk))
