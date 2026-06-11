"""Skill activation: the harness side of tool synthesis.

The agent writes a skill (SKILL.md + handler.py); the harness — not the agent —
installs declared pip dependencies and runs the skill's selftest. Failures
quarantine the skill (SKILL.md -> SKILL.md.failed) so a broken integration can
never poison the loader. The agent keeps zero shell access.
"""

from __future__ import annotations

import importlib.util
import re
import subprocess
import sys
import yaml
from dataclasses import dataclass
from pathlib import Path

PIP_TIMEOUT_SECS = 300
SELFTEST_TIMEOUT_SECS = 60
_FRONTMATTER = re.compile(r"\A---\s*\n(.*?)\n---\s*(\n|\Z)", re.DOTALL)


@dataclass(frozen=True)
class ActivationReport:
    skill: str
    ok: bool
    detail: str


def _meta(skill_md: Path) -> dict:
    match = _FRONTMATTER.match(skill_md.read_text(encoding="utf-8", errors="replace"))
    if not match:
        return {}
    try:
        return yaml.safe_load(match.group(1)) or {}
    except yaml.YAMLError:
        return {}


def _pip_install(packages: list[str]) -> tuple[bool, str]:
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-q", *packages],
        capture_output=True, text=True, timeout=PIP_TIMEOUT_SECS,
    )
    return result.returncode == 0, (result.stderr or result.stdout).strip()[-300:]


def _run_selftest(directory: Path, script: str, name: str) -> tuple[bool, str]:
    path = directory / script
    spec = importlib.util.spec_from_file_location(f"jetsonclaw_activate_{name}", path)
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception as e:
        return False, f"import failed: {type(e).__name__}: {e}"
    selftest = getattr(module, "selftest", None)
    if selftest is None:
        return True, "no selftest() — accepted on import alone"
    try:
        outcome = selftest()
        return True, str(outcome)[:200] or "selftest passed"
    except Exception as e:
        return False, f"selftest failed: {type(e).__name__}: {e}"


def activate_skills(skills_dir: str | Path,
                    only_since: float | None = None) -> list[ActivationReport]:
    """Install deps and validate every (or every recently-touched) skill.
    Quarantines failures. Safe to call repeatedly — idempotent for healthy skills."""
    root = Path(skills_dir).expanduser()
    if not root.is_dir():
        return []
    reports = []
    for skill_md in sorted(root.glob("*/SKILL.md")):
        if only_since is not None and skill_md.stat().st_mtime < only_since:
            continue
        meta = _meta(skill_md)
        name = str(meta.get("name", skill_md.parent.name))
        requires = meta.get("requires") or {}
        action = meta.get("action") or {}

        pip_packages = [str(p) for p in (requires.get("pip") or [])]
        if pip_packages:
            ok, detail = _pip_install(pip_packages)
            if not ok:
                skill_md.rename(skill_md.with_suffix(".md.failed"))
                reports.append(ActivationReport(name, False, f"pip: {detail}"))
                continue

        script = action.get("script")
        if script:
            try:
                ok, detail = _run_selftest(skill_md.parent, script, name)
            except Exception as e:  # subprocess timeout etc.
                ok, detail = False, str(e)[:200]
            if not ok:
                skill_md.rename(skill_md.with_suffix(".md.failed"))
                reports.append(ActivationReport(name, False, detail))
                continue
            reports.append(ActivationReport(name, True, detail))
        else:
            reports.append(ActivationReport(name, True, "command skill, no validation"))
    return reports
