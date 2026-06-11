"""Fast-path chat brain. Two protocols, one code path everywhere else:

- provider "ollama"  -> /api/generate (the on-device default, qwen2.5:3b)
- provider "openai"  -> any /v1/chat/completions endpoint: llama.cpp, vLLM,
  LM Studio, Groq, OpenRouter, Together, OpenAI itself

stdlib urllib only. Streaming matters: tokens are split into sentences as they
arrive so TTS starts speaking while the rest generates.
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import threading
import time
import urllib.error
import urllib.request
from typing import AsyncIterator, Iterator

from ..config import ChatConfig

_SENTENCE_END = re.compile(r"(?<=[.!?])\s+")
_STREAM_DONE = object()
_CACHE_MAX = 128


def split_complete_sentences(buffer: str) -> tuple[list[str], str]:
    """Split off finished sentences, returning (sentences, remainder)."""
    parts = _SENTENCE_END.split(buffer)
    if len(parts) <= 1:
        return [], buffer
    return [p.strip() for p in parts[:-1] if p.strip()], parts[-1]


class ChatBrain:
    def __init__(self, cfg: ChatConfig) -> None:
        self._cfg = cfg
        self._cache: dict[str, str] = {}

    # --- public API ---

    async def chat(self, text: str, system: str = "") -> str:
        key = text.strip().lower()
        if key in self._cache:
            return self._cache[key]
        try:
            response = await asyncio.to_thread(self._request, text, system)
        except Exception as e:
            return f"My local brain is offline: {e}"
        self._cache_put(key, response)
        return response

    async def stream_sentences(self, text: str, system: str = "") -> AsyncIterator[str]:
        """Yield complete sentences as the model generates them."""
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
                    self._cache_put(key, " ".join(full))
            except Exception as e:
                loop.call_soon_threadsafe(
                    queue.put_nowait, f"My local brain is offline: {e}")
            finally:
                loop.call_soon_threadsafe(queue.put_nowait, _STREAM_DONE)

        threading.Thread(target=worker, name="chat-stream", daemon=True).start()
        while True:
            item = await queue.get()
            if item is _STREAM_DONE:
                return
            yield item

    # --- payloads (pure, tested) ---

    def _system(self, extra: str) -> str:
        return f"{self._cfg.system_prompt}\n\n{extra}" if extra else self._cfg.system_prompt

    def payload(self, text: str, system: str, stream: bool) -> dict:
        if self._cfg.provider == "openai":
            return {
                "model": self._cfg.model,
                "messages": [
                    {"role": "system", "content": self._system(system)},
                    {"role": "user", "content": text},
                ],
                "stream": stream,
                "max_tokens": self._cfg.num_predict,
                "temperature": self._cfg.temperature,
            }
        return {
            "model": self._cfg.model,
            "prompt": text,
            "system": self._system(system),
            "stream": stream,
            # keep the model resident on Jetson shared memory
            "keep_alive": self._cfg.keep_alive,
            "options": {
                "temperature": self._cfg.temperature,
                "num_predict": self._cfg.num_predict,
            },
        }

    # --- blocking internals ---

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self._cfg.provider == "openai":
            key = os.environ.get(self._cfg.api_key_env, "")
            if key:
                headers["Authorization"] = f"Bearer {key}"
        return headers

    def _open(self, payload: dict):
        req = urllib.request.Request(
            self._cfg.url, data=json.dumps(payload).encode(), headers=self._headers())
        # Jetson shared memory: model load can transiently OOM (HTTP 500)
        # under cache pressure. One retry usually succeeds.
        for attempt in (1, 2):
            try:
                return urllib.request.urlopen(req, timeout=self._cfg.timeout_secs)
            except urllib.error.HTTPError as e:
                if e.code != 500 or attempt == 2:
                    raise
                time.sleep(2)

    def _request(self, text: str, system: str) -> str:
        with self._open(self.payload(text, system, False)) as resp:
            result = json.loads(resp.read().decode())
        if self._cfg.provider == "openai":
            return result["choices"][0]["message"]["content"].strip()
        return result.get("response", "").strip()

    def _stream_tokens(self, text: str, system: str) -> Iterator[str]:
        with self._open(self.payload(text, system, True)) as resp:
            for raw in resp:
                token = self._parse_stream_line(raw)
                if token is None:
                    return
                if token:
                    yield token

    def _parse_stream_line(self, raw: bytes) -> str | None:
        """One stream line -> token text, '' to skip, None to stop."""
        line = raw.strip()
        if not line:
            return ""
        if self._cfg.provider == "openai":
            if not line.startswith(b"data:"):
                return ""
            data = line[5:].strip()
            if data == b"[DONE]":
                return None
            try:
                msg = json.loads(data)
                return msg["choices"][0].get("delta", {}).get("content") or ""
            except (json.JSONDecodeError, KeyError, IndexError):
                return ""
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            return ""
        if msg.get("done"):
            return None
        return msg.get("response", "")

    def _cache_put(self, key: str, value: str) -> None:
        if len(self._cache) >= _CACHE_MAX:
            self._cache.pop(next(iter(self._cache)))
        self._cache[key] = value
