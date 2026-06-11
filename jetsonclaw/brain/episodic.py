"""Episodic memory: every interaction, logged and searchable.

Three layers, modeled loosely on human memory:
- episodes.jsonl   — raw what-happened-when (this file)
- memory/DATE.md   — daily summaries written during idle consolidation ("sleep")
- MEMORY.md        — consolidated long-term facts (semantic memory)

Search is keyword-overlap with recency boost — no vector DB, no GPU. At the
scale of one person's voice history, grep-class search wins on latency.
"""

from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

_WORD = re.compile(r"[a-z0-9']+")
_STOPWORDS = frozenset(
    "a an the is are was were be been i you he she it we they my your his her "
    "its our their me him them this that these those what which who whom when "
    "where why how do does did doing to of in on at by for with about and or "
    "not no yes so if then than too very can will just don't didn't".split())


def _keywords(text: str) -> set[str]:
    return {w for w in _WORD.findall(text.lower()) if w not in _STOPWORDS}


@dataclass(frozen=True)
class Episode:
    ts: float
    user: str
    reply: str
    intent: str

    @property
    def day(self) -> str:
        return datetime.fromtimestamp(self.ts).strftime("%Y-%m-%d")

    def render(self) -> str:
        when = datetime.fromtimestamp(self.ts).strftime("%a %Y-%m-%d %H:%M")
        return f"[{when}] user: {self.user} / assistant: {self.reply}"


class EpisodicStore:
    def __init__(self, memory_dir: str | Path) -> None:
        self.dir = Path(memory_dir).expanduser()
        self.path = self.dir / "episodes.jsonl"

    def append(self, user: str, reply: str, intent: str,
               ts: float | None = None) -> None:
        self.dir.mkdir(parents=True, exist_ok=True)
        record = {"ts": time.time() if ts is None else ts, "user": user,
                  "reply": reply[:1000], "intent": intent}
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    def all(self) -> list[Episode]:
        if not self.path.is_file():
            return []
        episodes = []
        with open(self.path, encoding="utf-8") as f:
            for line in f:
                try:
                    d = json.loads(line)
                    episodes.append(Episode(d["ts"], d["user"], d["reply"],
                                            d.get("intent", "")))
                except (json.JSONDecodeError, KeyError):
                    continue
        return episodes

    def search(self, query: str, limit: int = 3,
               now: float | None = None) -> list[Episode]:
        """Keyword overlap, recency-boosted. Skips the last few minutes so the
        current conversation (already in working memory) isn't echoed back."""
        words = _keywords(query)
        if not words:
            return []
        now = time.time() if now is None else now
        scored = []
        for ep in self.all():
            if now - ep.ts < 300:
                continue
            overlap = len(words & (_keywords(ep.user) | _keywords(ep.reply)))
            if overlap == 0:
                continue
            age_days = max(0.0, (now - ep.ts) / 86400)
            scored.append((overlap / (1 + age_days * 0.1), ep))
        scored.sort(key=lambda pair: pair[0], reverse=True)
        return [ep for _, ep in scored[:limit]]

    def on_day(self, day: str) -> list[Episode]:
        return [ep for ep in self.all() if ep.day == day]

    def unconsolidated_days(self, now: float | None = None) -> list[str]:
        """Past days that have episodes but no memory/DATE.md summary yet."""
        now = time.time() if now is None else now
        today = datetime.fromtimestamp(now).strftime("%Y-%m-%d")
        days = sorted({ep.day for ep in self.all() if ep.day < today})
        return [d for d in days if not (self.dir / f"{d}.md").is_file()]


_CONSOLIDATE_PROMPT = """Below is everything that happened between you and your owner on {day}.
Write two sections in plain markdown:

## Summary
3-6 bullet points of what happened that day, most important first.

## Facts
Bullet points of durable facts worth remembering long-term (preferences,
people, projects, decisions). Only include things that will still matter in a
month. If nothing qualifies, write "- none".

Transcript:
{transcript}"""


class Consolidator:
    """Sleep-time memory consolidation, run by the app when idle."""

    def __init__(self, store: EpisodicStore, brain, workspace) -> None:
        self._store = store
        self._brain = brain  # OllamaBrain
        self._workspace = workspace

    async def consolidate_one(self) -> str | None:
        """Consolidate the oldest unconsolidated day. Returns the day, or None."""
        days = self._store.unconsolidated_days()
        if not days:
            return None
        day = days[0]
        episodes = self._store.on_day(day)
        transcript = "\n".join(ep.render() for ep in episodes)[:6000]
        summary = await self._brain.chat(
            _CONSOLIDATE_PROMPT.format(day=day, transcript=transcript))
        if summary.startswith("My local brain is offline"):
            return None  # try again next idle window
        (self._store.dir / f"{day}.md").write_text(
            f"# {day}\n\n{summary}\n", encoding="utf-8")
        self._fold_facts(day, summary)
        return day

    def _fold_facts(self, day: str, summary: str) -> None:
        """Append the Facts section to long-term MEMORY.md (skip 'none')."""
        match = re.search(r"## Facts\s*\n(.*)", summary, re.DOTALL)
        if not match:
            return
        facts = [ln for ln in match.group(1).strip().splitlines()
                 if ln.strip().startswith("-") and "none" not in ln.lower()]
        if not facts:
            return
        memory_md = self._workspace.root / "MEMORY.md"
        existing = memory_md.read_text(encoding="utf-8") if memory_md.is_file() else ""
        new_facts = [f for f in facts if f.strip() not in existing]
        if new_facts:
            with open(memory_md, "a", encoding="utf-8") as f:
                f.write(f"\n<!-- consolidated {day} -->\n" + "\n".join(new_facts) + "\n")
