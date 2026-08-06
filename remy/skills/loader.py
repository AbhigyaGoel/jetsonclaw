"""Self-grown skills: SKILL.md files that hot-load — no restart, no selftest.

A skill is a directory under ~/.remy/skills/ containing SKILL.md with
YAML frontmatter (format borrowed from OpenClaw, simplified for voice):

    ---
    name: time
    description: tell the current time
    triggers:
      - what time is it
      - what's the time
    action:
      command: date +"%-I:%M %p"
    requires:
      bins: [date]
    ---
    Free-form notes for humans and agents.

`action.command` runs a shell snippet (utterance in $REMY_TEXT, stdout is
spoken). `action.script: handler.py` imports a sibling Python file and calls
`handle(text) -> str`. Skills are rescanned on every utterance with an mtime
cache, so "Jarvis, give yourself a skill" takes effect immediately.
"""

from __future__ import annotations

import importlib.util
import os
import re
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from ..redact import redact

COMMAND_TIMEOUT_SECS = 30
_FRONTMATTER = re.compile(r"\A---\s*\n(.*?)\n---\s*(\n|\Z)", re.DOTALL)


MIN_WATCH_INTERVAL_SECS = 60


@dataclass(frozen=True)
class DynamicSkill:
    name: str
    description: str
    triggers: tuple[re.Pattern, ...]
    directory: Path
    command: str | None = None
    script: str | None = None
    missing_bins: tuple[str, ...] = field(default=())
    missing_env: tuple[str, ...] = field(default=())
    credential: str = ""  # requires.credential: broker provides a short-lived token
    watch_interval: float | None = None  # run on a schedule; speak on changed output
    inject_keywords: tuple[str, ...] = ()  # push body into chat context on match
    body: str = ""  # markdown after the frontmatter

    def available(self) -> bool:
        return not self.missing_bins and not self.missing_env \
            and (self.command or self.script or self.inject_keywords)

    def matches(self, text: str) -> bool:
        return any(t.search(text) for t in self.triggers)

    def matches_inject(self, text: str) -> bool:
        lower = text.lower()
        return any(k in lower for k in self.inject_keywords)

    def converse(self, text: str) -> str | None:
        """Follow-up hook: script skills may define converse(text) -> str|None
        to claim the next utterance after they handle one (OVOS-style)."""
        if not self.script:
            return None
        path = self.directory / self.script
        spec = importlib.util.spec_from_file_location(
            f"remy_skill_{self.name}", path)
        module = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(module)
            handler = getattr(module, "converse", None)
            if handler is None:
                return None
            result = handler(text)
            return str(result) if result is not None else None
        except Exception:
            return None  # a broken converse never blocks normal routing

    def run(self, text: str) -> str:
        if self.command:
            return self._run_command(text)
        if self.script:
            return self._run_script(text)
        return f"Skill {self.name} has no action."

    def _run_command(self, text: str) -> str:
        try:
            result = subprocess.run(
                ["bash", "-c", self.command],
                env={"PATH": "/usr/local/bin:/usr/bin:/bin", "REMY_TEXT": text,
                     "HOME": str(Path.home())},
                capture_output=True, text=True, timeout=COMMAND_TIMEOUT_SECS,
                cwd=str(self.directory),
            )
        except subprocess.TimeoutExpired:
            return f"The {self.name} skill timed out."
        if result.returncode != 0:
            detail = redact((result.stderr or result.stdout).strip())[:120]
            return f"The {self.name} skill failed: {detail}"
        return result.stdout.strip() or "Done."

    def _run_script(self, text: str) -> str:
        path = self.directory / self.script
        spec = importlib.util.spec_from_file_location(
            f"remy_skill_{self.name}", path)
        module = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(module)
            return str(module.handle(text)).strip() or "Done."
        except Exception as e:
            return f"The {self.name} skill crashed: {type(e).__name__}: {e}"


def parse_skill(path: Path) -> DynamicSkill | None:
    """Parse one SKILL.md. Returns None for files that aren't valid skills."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
        match = _FRONTMATTER.match(text)
        if not match:
            return None
        meta = yaml.safe_load(match.group(1)) or {}
        body = text[match.end():].strip()
    except (OSError, yaml.YAMLError):
        return None

    name = str(meta.get("name", "")).strip()
    raw_triggers = meta.get("triggers") or []
    raw_watch = meta.get("watch")
    if not name or not isinstance(raw_triggers, list):
        return None

    triggers = []
    for raw in raw_triggers:
        try:
            triggers.append(re.compile(str(raw), re.IGNORECASE))
        except re.error:
            continue

    watch_interval = None
    if raw_watch is not None:
        raw_secs = raw_watch.get("interval_secs") if isinstance(raw_watch, dict) else raw_watch
        try:
            watch_interval = max(float(raw_secs), MIN_WATCH_INTERVAL_SECS)
        except (TypeError, ValueError):
            pass

    raw_inject = meta.get("inject") or []
    inject_keywords = tuple(str(k).lower() for k in raw_inject) \
        if isinstance(raw_inject, list) else ()

    # a skill needs at least one way to fire: a phrase, a schedule, or injection
    if not triggers and watch_interval is None and not inject_keywords:
        return None

    action = meta.get("action") or {}
    requires = meta.get("requires") or {}
    bins = [str(b) for b in (requires.get("bins") or [])]
    missing = tuple(b for b in bins if shutil.which(b) is None)
    env_vars = [str(v) for v in (requires.get("env") or [])]
    missing_env = tuple(v for v in env_vars if not os.environ.get(v))
    credential = str(requires.get("credential") or "")

    return DynamicSkill(
        name=name,
        description=str(meta.get("description", "")),
        triggers=tuple(triggers),
        directory=path.parent,
        command=action.get("command"),
        script=action.get("script"),
        missing_bins=missing,
        missing_env=missing_env,
        credential=credential,
        watch_interval=watch_interval,
        inject_keywords=inject_keywords,
        body=body,
    )


class SkillLoader:
    """Scans the skills dir on demand, caching parses by mtime."""

    def __init__(self, skills_dir: str | Path) -> None:
        self._dir = Path(skills_dir).expanduser()
        self._cache: dict[Path, tuple[float, DynamicSkill | None]] = {}

    def scan(self) -> list[DynamicSkill]:
        if not self._dir.is_dir():
            return []
        skills = []
        for skill_md in sorted(self._dir.glob("*/SKILL.md")):
            try:
                mtime = skill_md.stat().st_mtime
            except OSError:
                continue
            cached = self._cache.get(skill_md)
            if cached is None or cached[0] != mtime:
                self._cache[skill_md] = (mtime, parse_skill(skill_md))
            skill = self._cache[skill_md][1]
            if skill is not None and skill.available():
                skills.append(skill)
        return skills

    def find(self, text: str) -> DynamicSkill | None:
        return next((s for s in self.scan() if s.matches(text)), None)

    def watchers(self) -> list[DynamicSkill]:
        return [s for s in self.scan() if s.watch_interval is not None]

    def knowledge_for(self, text: str, cap: int = 2000) -> str:
        """Bodies of inject-matching skills, pushed into chat context."""
        parts = [s.body[:cap] for s in self.scan()
                 if s.inject_keywords and s.matches_inject(text) and s.body]
        return "\n\n".join(parts)

    def by_name(self, name: str) -> DynamicSkill | None:
        return next((s for s in self.scan() if s.name == name), None)

    def catalog(self) -> str:
        """One line per skill — injected into agent briefs so JARVIS knows
        what it can already do."""
        return "\n".join(f"- {s.name}: {s.description}" for s in self.scan())
