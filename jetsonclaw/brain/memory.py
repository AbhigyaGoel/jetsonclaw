"""Short-term conversation memory — the difference between an assistant and a
magic 8-ball. Recent turns are replayed into the local LLM prompt so
"what about tomorrow?" works after a weather question."""

from __future__ import annotations

import time
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Turn:
    user: str
    assistant: str
    ts: float


@dataclass
class ConversationMemory:
    max_turns: int = 6
    ttl_secs: float = 600.0
    _turns: list[Turn] = field(default_factory=list)

    def add(self, user: str, assistant: str, now: float | None = None) -> None:
        ts = time.time() if now is None else now
        self._turns = (self._turns + [Turn(user, assistant, ts)])[-self.max_turns:]

    def recent(self, now: float | None = None) -> list[Turn]:
        cutoff = (time.time() if now is None else now) - self.ttl_secs
        return [t for t in self._turns if t.ts >= cutoff]

    def clear(self) -> None:
        self._turns = []

    def as_prompt(self, new_text: str, now: float | None = None) -> str:
        """Render history + the new utterance for a completion-style endpoint
        (/api/generate is more reliable than /api/chat on small qwen models)."""
        turns = self.recent(now)
        if not turns:
            return new_text
        lines = []
        for t in turns:
            lines.append(f"User: {t.user}")
            lines.append(f"JARVIS: {t.assistant}")
        lines.append(f"User: {new_text}")
        lines.append("JARVIS:")
        return "Previous conversation:\n" + "\n".join(lines)
