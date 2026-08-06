"""Text-to-speech via the Piper binary, run out-of-process and streamed to aplay.

REMY is MIT; Piper's current engine (piper1-gpl) is GPL-3.0. We never import it —
we exec the `piper` binary and pipe its raw audio to aplay, so the GPL stays on
the far side of a process boundary. See remy/licensing.py for the guard that
enforces "no GPL in-process".

Latency playbook for the Orin (CPU is plenty for TTS):
- one piper process per utterance, streaming; playback starts on the first chunk
- warm up once at startup so the first real reply isn't slow
- interrupt by killing the piper->aplay pipe, not by tearing down a model
"""

from __future__ import annotations

import json
import shutil
import subprocess
import threading
from pathlib import Path

DEFAULT_SAMPLE_RATE = 22050


def piper_cmd(binary: str, model_path: str | Path, length_scale: float) -> list[str]:
    """Argv for a streaming piper synthesis — no shell, injection-safe. Reads
    text on stdin, writes raw S16_LE mono PCM to stdout."""
    return [binary, "--model", str(model_path), "--output-raw",
            "--length-scale", str(length_scale)]


def read_sample_rate(model_path: str | Path) -> int:
    """Piper voices ship a companion <model>.onnx.json carrying the sample rate."""
    meta = Path(f"{model_path}.json")
    try:
        data = json.loads(meta.read_text(encoding="utf-8"))
        return int(data["audio"]["sample_rate"])
    except (OSError, ValueError, KeyError, TypeError):
        return DEFAULT_SAMPLE_RATE


class Speaker:
    def __init__(self, voice: str, voices_dir: str, speaker_device: str,
                 length_scale: float = 1.0, enabled: bool = True,
                 binary: str = "piper") -> None:
        self._voice_name = voice
        self._voices_dir = Path(voices_dir).expanduser()
        self._device = speaker_device
        self._length_scale = length_scale
        self._binary = binary
        self._sample_rate = DEFAULT_SAMPLE_RATE
        self._piper: subprocess.Popen | None = None
        self._sink: subprocess.Popen | None = None
        self._lock = threading.Lock()
        self.enabled = enabled

    @property
    def model_path(self) -> Path:
        return self._voices_dir / f"{self._voice_name}.onnx"

    def load(self) -> bool:
        """Verify the piper binary and voice are present. Returns False (and
        disables TTS) if either is missing — REMY stays usable, just silent."""
        if not self.enabled:
            return False
        if shutil.which(self._binary) is None or not self.model_path.is_file():
            self.enabled = False
            return False
        self._sample_rate = read_sample_rate(self.model_path)
        self._warmup()
        return True

    def _warmup(self) -> None:
        """Best-effort: prime the OS page cache so the first reply isn't slow."""
        try:
            proc = subprocess.Popen(
                piper_cmd(self._binary, self.model_path, self._length_scale),
                stdin=subprocess.PIPE, stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL)
            proc.communicate(b"Ready.\n", timeout=30)
        except Exception:
            pass

    def available(self) -> bool:
        return self.enabled

    def speak(self, text: str) -> None:
        """Synthesize and play, blocking until playback finishes or stop()."""
        if not self.available() or not text.strip():
            return
        self.stop()
        try:
            piper = subprocess.Popen(
                piper_cmd(self._binary, self.model_path, self._length_scale),
                stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL)
            sink = subprocess.Popen(
                [
                    "aplay", "-D", self._device, "-q", "-t", "raw",
                    "-f", "S16_LE", "-r", str(self._sample_rate), "-c", "1",
                ],
                stdin=piper.stdout, stderr=subprocess.DEVNULL,
            )
        except (OSError, ValueError):
            self.enabled = False
            return
        # aplay owns the read end now; close our copy so EOF propagates.
        if piper.stdout is not None:
            piper.stdout.close()
        with self._lock:
            self._piper, self._sink = piper, sink
        try:
            assert piper.stdin is not None
            piper.stdin.write(text.strip().encode("utf-8") + b"\n")
            piper.stdin.close()
            sink.wait()
        except (BrokenPipeError, OSError):
            pass  # interrupted mid-write
        finally:
            with self._lock:
                if self._piper is piper:
                    self._piper = None
                if self._sink is sink:
                    self._sink = None
            if piper.poll() is None:
                piper.kill()

    def stop(self) -> None:
        """Interrupt playback (e.g. wake word while JARVIS is talking)."""
        with self._lock:
            for proc in (self._sink, self._piper):
                if proc is not None and proc.poll() is None:
                    proc.kill()
            self._sink = None
            self._piper = None
