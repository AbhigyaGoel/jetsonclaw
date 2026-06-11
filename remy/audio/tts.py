"""Text-to-speech via Piper (piper1-gpl Python API), streamed to aplay.

Latency playbook for the Orin (CPU is plenty for TTS):
- load the voice model ONCE at startup, never per-utterance
- warm up with a silent synthesis so the first real reply isn't slow
- split text into sentences and start playback on the first chunk
- interrupt by killing the aplay sink, not the model
"""

from __future__ import annotations

import re
import subprocess
import threading
from pathlib import Path

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")


class Speaker:
    def __init__(self, voice: str, voices_dir: str, speaker_device: str,
                 length_scale: float = 1.0, enabled: bool = True) -> None:
        self._voice_name = voice
        self._voices_dir = Path(voices_dir).expanduser()
        self._device = speaker_device
        self._length_scale = length_scale
        self._voice = None
        self._sample_rate = 22050
        self._sink: subprocess.Popen | None = None
        self._lock = threading.Lock()
        self.enabled = enabled

    @property
    def model_path(self) -> Path:
        return self._voices_dir / f"{self._voice_name}.onnx"

    def load(self) -> bool:
        """Load the voice model. Returns False (and disables TTS) on failure."""
        if not self.enabled:
            return False
        try:
            from piper import PiperVoice  # heavy import, defer

            self._voice = PiperVoice.load(str(self.model_path))
            rate = getattr(getattr(self._voice, "config", None), "sample_rate", None)
            if rate:
                self._sample_rate = int(rate)
            self._warmup()
            return True
        except Exception:
            self.enabled = False
            return False

    def _warmup(self) -> None:
        for _ in self._synthesize("Ready."):
            pass

    def _synthesize(self, text: str):
        try:
            from piper import SynthesisConfig

            syn_cfg = SynthesisConfig(length_scale=self._length_scale)
            yield from self._voice.synthesize(text, syn_config=syn_cfg)
        except (ImportError, TypeError):
            yield from self._voice.synthesize(text)

    def available(self) -> bool:
        return self.enabled and self._voice is not None

    def speak(self, text: str) -> None:
        """Synthesize and play, blocking until playback finishes or stop()."""
        if not self.available() or not text.strip():
            return
        self.stop()
        sink = subprocess.Popen(
            [
                "aplay", "-D", self._device, "-q", "-t", "raw",
                "-f", "S16_LE", "-r", str(self._sample_rate), "-c", "1",
            ],
            stdin=subprocess.PIPE, stderr=subprocess.DEVNULL,
        )
        with self._lock:
            self._sink = sink
        try:
            for sentence in _SENTENCE_SPLIT.split(text.strip()):
                if not sentence:
                    continue
                for chunk in self._synthesize(sentence):
                    if sink.poll() is not None:  # interrupted
                        return
                    sink.stdin.write(chunk.audio_int16_bytes)
            sink.stdin.close()
            sink.wait()
        except (BrokenPipeError, OSError):
            pass  # interrupted mid-write
        finally:
            with self._lock:
                if self._sink is sink:
                    self._sink = None

    def stop(self) -> None:
        """Interrupt playback (e.g. wake word while JARVIS is talking)."""
        with self._lock:
            if self._sink is not None and self._sink.poll() is None:
                self._sink.kill()
            self._sink = None
