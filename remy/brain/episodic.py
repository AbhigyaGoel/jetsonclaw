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
from datetime import datetime
from pathlib import Path

from ..redact import redact

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
        # Redact secrets before they reach disk (and the consolidation chain that
        # feeds daily summaries and MEMORY.md). Redact before truncating so a
        # token straddling the 1000-char cut is still caught.
        record = {"ts": time.time() if ts is None else ts, "user": redact(user),
                  "reply": redact(reply)[:1000], "intent": intent}
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

    WORKING_TTL_SECS = 600.0
    WORKING_MAX_TURNS = 6

    def recent_turns(self, now: float | None = None,
                     floor: float = 0.0) -> list[Episode]:
        """Working memory: the last few turns, unless cleared past `floor`."""
        now = time.time() if now is None else now
        cutoff = max(now - self.WORKING_TTL_SECS, floor)
        recent = [ep for ep in self.all() if ep.ts >= cutoff]
        return recent[-self.WORKING_MAX_TURNS:]

    def as_prompt(self, new_text: str, now: float | None = None,
                  floor: float = 0.0) -> str:
        """Render working memory + the new utterance for a completion endpoint."""
        turns = self.recent_turns(now, floor)
        if not turns:
            return new_text
        lines = []
        for t in turns:
            lines.append(f"User: {t.user}")
            lines.append(f"Assistant: {t.reply}")
        lines.append(f"User: {new_text}")
        lines.append("Assistant:")
        return "Previous conversation:\n" + "\n".join(lines)

    def search(self, query: str, limit: int = 3,
               now: float | None = None) -> list[Episode]:
        """Keyword overlap, recency-boosted. Skips the working-memory window so
        the current conversation isn't echoed back into itself."""
        words = _keywords(query)
        if not words:
            return []
        now = time.time() if now is None else now
        scored = []
        for ep in self.all():
            if now - ep.ts < self.WORKING_TTL_SECS:
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

    def search_summaries(self, query: str, limit: int = 4) -> list[str]:
        """Matching lines from consolidated daily summaries (memory/DATE.md),
        tagged with their date so temporal questions can be answered."""
        words = _keywords(query)
        if not words or not self.dir.is_dir():
            return []
        hits = []
        for path in sorted(self.dir.glob("????-??-??.md"), reverse=True):
            for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
                if line.strip().startswith("-") and words & _keywords(line):
                    hits.append(f"[{path.stem}] {line.strip()}")
                    if len(hits) >= limit:
                        return hits
        return hits

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
        self._brain = brain  # ChatBrain
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
