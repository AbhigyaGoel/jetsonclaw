"""Self-grown skills: SKILL.md files that hot-load — no restart, no selftest.

A skill is a directory under ~/.jetsonclaw/skills/ containing SKILL.md with
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

`action.command` runs a shell snippet (utterance in $JARVIS_TEXT, stdout is
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
    watch_interval: float | None = None  # run on a schedule; speak on changed output

    def available(self) -> bool:
        return not self.missing_bins and not self.missing_env \
            and (self.command or self.script)

    def matches(self, text: str) -> bool:
        return any(t.search(text) for t in self.triggers)

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
                env={"PATH": "/usr/local/bin:/usr/bin:/bin", "JARVIS_TEXT": text,
                     "HOME": str(Path.home())},
                capture_output=True, text=True, timeout=COMMAND_TIMEOUT_SECS,
                cwd=str(self.directory),
            )
        except subprocess.TimeoutExpired:
            return f"The {self.name} skill timed out."
        if result.returncode != 0:
            detail = (result.stderr or result.stdout).strip()[:120]
            return f"The {self.name} skill failed: {detail}"
        return result.stdout.strip() or "Done."

    def _run_script(self, text: str) -> str:
        path = self.directory / self.script
        spec = importlib.util.spec_from_file_location(
            f"jetsonclaw_skill_{self.name}", path)
        module = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(module)
            return str(module.handle(text)).strip() or "Done."
        except Exception as e:
            return f"The {self.name} skill crashed: {type(e).__name__}: {e}"


def parse_skill(path: Path) -> DynamicSkill | None:
    """Parse one SKILL.md. Returns None for files that aren't valid skills."""
    try:
        match = _FRONTMATTER.match(path.read_text(encoding="utf-8", errors="replace"))
        if not match:
            return None
        meta = yaml.safe_load(match.group(1)) or {}
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

    # a skill needs at least one way to fire: a trigger phrase or a schedule
    if not triggers and watch_interval is None:
        return None

    action = meta.get("action") or {}
    requires = meta.get("requires") or {}
    bins = [str(b) for b in (requires.get("bins") or [])]
    missing = tuple(b for b in bins if shutil.which(b) is None)
    env_vars = [str(v) for v in (requires.get("env") or [])]
    missing_env = tuple(v for v in env_vars if not os.environ.get(v))

    return DynamicSkill(
        name=name,
        description=str(meta.get("description", "")),
        triggers=tuple(triggers),
        directory=path.parent,
        command=action.get("command"),
        script=action.get("script"),
        missing_bins=missing,
        missing_env=missing_env,
        watch_interval=watch_interval,
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

    def catalog(self) -> str:
        """One line per skill — injected into agent briefs so JARVIS knows
        what it can already do."""
        return "\n".join(f"- {s.name}: {s.description}" for s in self.scan())
