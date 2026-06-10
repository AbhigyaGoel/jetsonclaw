"""Fast-path chat via local ollama. stdlib urllib in a thread — no extra deps."""

from __future__ import annotations

import asyncio
import json
import time
import urllib.error
import urllib.request

from ..config import OllamaConfig


class OllamaBrain:
    def __init__(self, cfg: OllamaConfig) -> None:
        self._cfg = cfg
        self._cache: dict[str, str] = {}

    async def chat(self, text: str, system: str = "") -> str:
        key = text.strip().lower()
        if key in self._cache:
            return self._cache[key]
        try:
            response = await asyncio.to_thread(self._request, text, system)
        except Exception as e:
            return f"My local brain is offline: {e}"
        self._cache[key] = response
        return response

    def _request(self, text: str, system: str = "") -> str:
        full_system = self._cfg.system_prompt
        if system:
            full_system = f"{full_system}\n\n{system}"
        payload = json.dumps({
            "model": self._cfg.model,
            "prompt": text,
            "system": full_system,
            "stream": False,
            "options": {
                "temperature": self._cfg.temperature,
                "num_predict": self._cfg.num_predict,
            },
        }).encode()
        req = urllib.request.Request(
            self._cfg.url, data=payload,
            headers={"Content-Type": "application/json"},
        )
        # Shared CPU/GPU memory on Jetson: model load can transiently OOM
        # (HTTP 500) under cache pressure — one retry usually succeeds.
        for attempt in (1, 2):
            try:
                with urllib.request.urlopen(req, timeout=self._cfg.timeout_secs) as resp:
                    result = json.loads(resp.read().decode())
                return result.get("response", "").strip()
            except urllib.error.HTTPError as e:
                if e.code != 500 or attempt == 2:
                    raise
                time.sleep(2)
        return ""
