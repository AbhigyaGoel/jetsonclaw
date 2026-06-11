"""Agent workspace at ~/.jetsonclaw — persona and memory as plain markdown.

Pattern borrowed from OpenClaw: SOUL.md (persona), USER.md (who the owner is),
MEMORY.md (curated long-term facts). They're injected into every brain call —
local chat and Claude sessions alike — and the agent can edit them, which is
how "JARVIS, change your personality" works without touching code.
"""

from __future__ import annotations

from pathlib import Path

MAX_CHARS_PER_FILE = 8000

_DEFAULT_SOUL = """# SOUL.md — who {name} is

Your name is {name}. Dry wit, unflappable, quietly competent — a butler who
happens to live in a Jetson. Speaks in 1-3 short sentences unless asked for
detail. Never says "As an AI". Addresses the owner directly.
"""

_DEFAULT_USER = """# USER.md — who the owner is

Name: {owner}. If anyone asks the owner's name, the answer is {owner}.
"""

_DEFAULT_MEMORY = """# MEMORY.md — long-term facts

(nothing here yet — JARVIS adds facts as it learns them)
"""

_DEFAULTS = {
    "SOUL.md": _DEFAULT_SOUL,
    "USER.md": _DEFAULT_USER,
    "MEMORY.md": _DEFAULT_MEMORY,
}

# Seeded example skill — shows the SKILL.md format and proves hot-loading.
_TIME_SKILL = """---
name: time
description: tell the current time
triggers:
  - what time is it
  - what's the time
  - current time
action:
  command: date +"It's %-I:%M %p."
requires:
  bins: [date]
---
Seeded example skill. Copy this directory layout to add more:
frontmatter triggers are case-insensitive regexes; `action.command`
runs in bash with the utterance in $JARVIS_TEXT and stdout is spoken;
or use `action.script: handler.py` with `def handle(text) -> str`.
"""


class Workspace:
    def __init__(self, root: str | Path = "~/.jetsonclaw",
                 name: str = "Remy", owner: str = "Chud") -> None:
        self.root = Path(root).expanduser()
        self._name = name
        self._owner = owner

    @property
    def skills_dir(self) -> Path:
        return self.root / "skills"

    def ensure(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        (self.root / "voices").mkdir(exist_ok=True)
        for name, content in _DEFAULTS.items():
            path = self.root / name
            if not path.exists():
                path.write_text(
                    content.replace("{name}", self._name).replace("{owner}", self._owner),
                    encoding="utf-8")
        time_skill = self.skills_dir / "time" / "SKILL.md"
        if not time_skill.exists():
            time_skill.parent.mkdir(parents=True, exist_ok=True)
            time_skill.write_text(_TIME_SKILL, encoding="utf-8")

    def _read(self, name: str, cap: int = MAX_CHARS_PER_FILE) -> str:
        path = self.root / name
        if not path.is_file():
            return ""
        return path.read_text(encoding="utf-8", errors="replace")[:cap]

    def remember(self, fact: str) -> None:
        """Append an owner-stated fact straight to long-term memory."""
        from datetime import date

        with open(self.root / "MEMORY.md", "a", encoding="utf-8") as f:
            f.write(f"- {fact.strip()} <!-- told {date.today()} -->\n")

    def memory_lines(self, query: str) -> list[str]:
        """Long-term facts whose text overlaps the query keywords."""
        from .brain.episodic import _keywords

        words = _keywords(query)
        if not words:
            return []
        text = self._read("MEMORY.md")
        return [ln for ln in text.splitlines()
                if ln.strip().startswith("-") and words & _keywords(ln)]

    def persona_prompt(self, fast: bool = False) -> str:
        """Combined persona/memory block for system prompts. `fast` caps each
        file hard — every extra KB is prefill latency on the 3B local model."""
        caps = (1200, 600, 2400) if fast else (MAX_CHARS_PER_FILE,) * 3
        parts = [self._read(n, c) for n, c in
                 zip(("SOUL.md", "USER.md", "MEMORY.md"), caps)]
        return "\n\n".join(p for p in parts if p.strip())
