"""Fast-path chat via local ollama — stdlib urllib only.

Streaming matters: tokens are split into sentences as they arrive so TTS can
start speaking the first sentence while the rest is still generating. That's
the difference between ~1s and ~5s to first word.
"""

from __future__ import annotations

import asyncio
import json
import re
import threading
import time
import urllib.error
import urllib.request
from typing import AsyncIterator

from ..config import OllamaConfig

_SENTENCE_END = re.compile(r"(?<=[.!?])\s+")
_STREAM_DONE = object()


def split_complete_sentences(buffer: str) -> tuple[list[str], str]:
    """Split off finished sentences, returning (sentences, remainder)."""
    parts = _SENTENCE_END.split(buffer)
    if len(parts) <= 1:
        return [], buffer
    return [p.strip() for p in parts[:-1] if p.strip()], parts[-1]


class OllamaBrain:
    def __init__(self, cfg: OllamaConfig) -> None:
        self._cfg = cfg
        self._cache: dict[str, str] = {}

    async def chat(self, text: str, system: str = "") -> str:
        """Non-streaming completion (kept for cached/simple paths)."""
        key = text.strip().lower()
        if key in self._cache:
            return self._cache[key]
        try:
            response = await asyncio.to_thread(self._request, text, system, False)
        except Exception as e:
            return f"My local brain is offline: {e}"
        self._cache[key] = response
        return response

    async def stream_sentences(self, text: str, system: str = "") -> AsyncIterator[str]:
        """Yield complete sentences as the model generates them. Falls back to
        a single error sentence if ollama is unreachable."""
        key = text.strip().lower()
        if key in self._cache:
            yield self._cache[key]
            return

        queue: asyncio.Queue = asyncio.Queue()
        loop = asyncio.get_running_loop()

        def worker() -> None:
            buffer, full = "", []
            try:
                for token in self._stream_tokens(text, system):
                    buffer += token
                    sentences, buffer = split_complete_sentences(buffer)
                    for s in sentences:
                        full.append(s)
                        loop.call_soon_threadsafe(queue.put_nowait, s)
                if buffer.strip():
                    full.append(buffer.strip())
                    loop.call_soon_threadsafe(queue.put_nowait, buffer.strip())
                if full:
                    self._cache[key] = " ".join(full)
            except Exception as e:
                loop.call_soon_threadsafe(
                    queue.put_nowait, f"My local brain is offline: {e}")
            finally:
                loop.call_soon_threadsafe(queue.put_nowait, _STREAM_DONE)

        threading.Thread(target=worker, name="ollama-stream", daemon=True).start()
        while True:
            item = await queue.get()
            if item is _STREAM_DONE:
                return
            yield item

    # --- blocking internals ---

    def _payload(self, text: str, system: str, stream: bool) -> bytes:
        full_system = self._cfg.system_prompt
        if system:
            full_system = f"{full_system}\n\n{system}"
        return json.dumps({
            "model": self._cfg.model,
            "prompt": text,
            "system": full_system,
            "stream": stream,
            "options": {
                "temperature": self._cfg.temperature,
                "num_predict": self._cfg.num_predict,
            },
        }).encode()

    def _open(self, payload: bytes):
        req = urllib.request.Request(
            self._cfg.url, data=payload,
            headers={"Content-Type": "application/json"},
        )
        # Shared CPU/GPU memory on Jetson: model load can transiently OOM
        # (HTTP 500) under cache pressure — one retry usually succeeds.
        for attempt in (1, 2):
            try:
                return urllib.request.urlopen(req, timeout=self._cfg.timeout_secs)
            except urllib.error.HTTPError as e:
                if e.code != 500 or attempt == 2:
                    raise
                time.sleep(2)

    def _request(self, text: str, system: str, stream: bool) -> str:
        with self._open(self._payload(text, system, False)) as resp:
            result = json.loads(resp.read().decode())
        return result.get("response", "").strip()

    def _stream_tokens(self, text: str, system: str):
        with self._open(self._payload(text, system, True)) as resp:
            for raw in resp:
                try:
                    msg = json.loads(raw.decode())
                except json.JSONDecodeError:
                    continue
                token = msg.get("response", "")
                if token:
                    yield token
                if msg.get("done"):
                    return
