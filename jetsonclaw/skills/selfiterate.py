"""Voice-driven self-modification: "Jarvis, upgrade yourself ..."

Flow: snapshot HEAD -> headless Claude Code session edits this repo ->
smoke test (`python3 -m jetsonclaw --selftest`) -> commit + record
last-known-good + restart, or hard-reset on failure. "Undo that" reverts
the most recent jarvis: commit.
"""

from __future__ import annotations

import asyncio
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

from ..brain.claude import ClaudeBridge
from ..events import EventBus, EventType
from ..supervisor import BootGuard, _git
from .activate import activate_skills
from .loader import SkillLoader

COMMIT_PREFIX = "self: "  # name-agnostic — survives assistant renames

_AGENT_BRIEF = """You are modifying JetsonClaw, the voice assistant you are running inside of.

PREFER A WORKSPACE SKILL when adding a new voice capability: create
~/.jetsonclaw/skills/<name>/SKILL.md (YAML frontmatter: name, description,
triggers as regex list, action.command shell snippet OR action.script
handler.py with `def handle(text) -> str`, optional requires.bins). Workspace
skills hot-load instantly — no restart, no selftest. See
~/.jetsonclaw/skills/time/ for the format. Only edit repo code when the
instruction requires changing core behavior.

FOR REAL INTEGRATIONS (third-party APIs, anything needing pip packages):
- Research the API with WebFetch/WebSearch — read the actual docs, don't guess.
- Write a proper Python module as action.script handler.py. Declare pip
  dependencies in frontmatter as `requires: {pip: [package1, package2]}` —
  the harness installs them after you finish (you have no shell).
- Include `def selftest() -> str` in handler.py that makes one cheap REAL call
  to verify the integration works (e.g. fetch the authed user's profile).
  The harness runs it; if it fails, your skill is quarantined and the owner
  is told. Read any needed API keys from a `config.yaml` next to handler.py,
  and if a key is missing, make selftest() raise with a clear one-line
  instruction for where the owner should paste it.

Rules:
- Keep changes minimal and focused on the instruction.
- This runs on a Jetson Orin Nano: Python 3.10, numpy<2, no PyAudio (arecord only).
- Do NOT run the app, install packages, or touch git — the harness handles commits and testing.
- If you edit repo code, `python3 -m jetsonclaw --selftest` must still pass
  (it imports every module and runs the unit tests).
- End with one short spoken-style sentence describing what you did.
"""


@dataclass(frozen=True)
class IterationResult:
    ok: bool
    message: str
    restart: bool = False


def append_evolution(journal: Path, instruction: str, outcome: str,
                     ref: str, ts: float | None = None) -> None:
    """One auditable line per self-change: when, what was asked, what happened.
    'Why did you change yourself?' gets answered from this file, not vibes."""
    when = time.strftime("%Y-%m-%d %H:%M", time.localtime(ts))
    entry = (f"\n## {when} ({ref})\n"
             f"asked: {instruction.strip()}\n"
             f"result: {outcome.strip()[:300]}\n")
    journal.parent.mkdir(parents=True, exist_ok=True)
    with open(journal, "a", encoding="utf-8") as f:
        if journal.stat().st_size == 0:
            f.write("# EVOLUTION.md - every self-modification, in order\n")
        f.write(entry)


class SelfIterateSkill:
    def __init__(self, bridge: ClaudeBridge, guard: BootGuard,
                 repo_dir: str | Path, bus: EventBus,
                 skills_dir: str | Path | None = None) -> None:
        self._bridge = bridge
        self._guard = guard
        self._repo = Path(repo_dir).expanduser()
        self._bus = bus
        self._skills_dir = skills_dir

    async def iterate(self, instruction: str) -> IterationResult:
        if not self._bridge.available():
            return IterationResult(False, "My agentic brain isn't installed yet, sir.")

        before = await asyncio.to_thread(_git, self._repo, "rev-parse", "HEAD")
        started_at = time.time()
        self._bus.publish(EventType.AGENT_START, task=instruction, kind="self-iterate")

        brief = _AGENT_BRIEF
        if self._skills_dir is not None:
            catalog = await asyncio.to_thread(SkillLoader(self._skills_dir).catalog)
            if catalog:
                brief += f"\nSkills that already exist (extend, don't duplicate):\n{catalog}\n"

        result_text = ""
        async for line in self._bridge.run(instruction, workdir=self._repo,
                                           system_append=brief):
            self._bus.publish(EventType.AGENT_OUTPUT, kind=line.kind, text=line.text)
            if line.kind == "result":
                result_text = line.text
            if line.kind == "error":
                await self._discard(before)
                return IterationResult(False, f"That didn't work: {line.text[:120]}")

        # Activate any skills the agent wrote/touched: harness installs pip
        # deps and runs selftests — failures are quarantined, never loaded.
        activation_note = ""
        if self._skills_dir is not None:
            reports = await asyncio.to_thread(
                activate_skills, self._skills_dir, started_at - 1)
            for r in reports:
                self._bus.publish(EventType.AGENT_OUTPUT, kind="tool",
                                  text=f"activate {r.skill}: {'ok' if r.ok else r.detail}")
            failed = [r for r in reports if not r.ok]
            if failed:
                activation_note = (f" But the {failed[0].skill} skill failed its "
                                   f"selftest and was quarantined: {failed[0].detail}")

        changed = await asyncio.to_thread(_git, self._repo, "status", "--porcelain")
        if not changed:
            # Workspace-skill path: nothing in the repo changed, no restart needed.
            summary = result_text.strip().split("\n")[-1][:200] if result_text else \
                "Done — no code changes were needed."
            self._bus.publish(EventType.AGENT_DONE, ok=True, detail="workspace-only change")
            self._journal(instruction, summary, "workspace")
            return IterationResult(True, summary + activation_note)

        # Repair before rollback: one bounded fix attempt with the failure
        # output fed back to the same session. Reverting is the last resort.
        ok, test_output = await asyncio.to_thread(self._smoke_test)
        if not ok:
            self._bus.publish(EventType.AGENT_OUTPUT, kind="error",
                              text=f"selftest failed, attempting repair: {test_output[-200:]}")
            repair_prompt = (f"Your change failed the selftest. Output:\n"
                             f"{test_output[-4000:]}\n\nFix the failure. "
                             f"Do not weaken or delete tests to make them pass.")
            async for line in self._bridge.run(repair_prompt, workdir=self._repo,
                                               continue_session=True):
                self._bus.publish(EventType.AGENT_OUTPUT, kind=line.kind, text=line.text)
            ok, test_output = await asyncio.to_thread(self._smoke_test)

        if not ok:
            await self._discard(before)
            self._bus.publish(EventType.AGENT_DONE, ok=False, detail=test_output[-800:])
            return IterationResult(
                False, "The change failed my self-test twice, so I threw it away.")

        await asyncio.to_thread(self._commit, instruction)
        self._guard.record_good(before)  # the commit we can fall back to
        head = await asyncio.to_thread(_git, self._repo, "rev-parse", "--short", "HEAD")
        self._journal(instruction, result_text or "tests passed", head)
        self._bus.publish(EventType.AGENT_DONE, ok=True, detail="committed, restarting")
        return IterationResult(True, "Done and tested. Restarting with the upgrade.", restart=True)

    async def rollback(self) -> IterationResult:
        last_msg = await asyncio.to_thread(_git, self._repo, "log", "-1", "--format=%s")
        if not last_msg.startswith(COMMIT_PREFIX):
            return IterationResult(False, "The last change wasn't one of mine — not touching it.")
        await asyncio.to_thread(_git, self._repo, "reset", "--hard", "HEAD~1")
        return IterationResult(True, "Reverted my last change. Restarting.", restart=True)

    def _journal(self, instruction: str, outcome: str, ref: str) -> None:
        if self._skills_dir is not None:
            journal = Path(self._skills_dir).expanduser().parent / "EVOLUTION.md"
            try:
                append_evolution(journal, instruction, outcome, ref)
            except OSError:
                pass  # journaling must never break an iteration

    # --- blocking helpers (run in threads) ---

    def _smoke_test(self) -> tuple[bool, str]:
        result = subprocess.run(
            [sys.executable, "-m", "jetsonclaw", "--selftest"],
            cwd=str(self._repo), capture_output=True, text=True, timeout=300,
        )
        return result.returncode == 0, result.stdout + result.stderr

    def _commit(self, instruction: str) -> None:
        _git(self._repo, "add", "-A")
        summary = instruction.strip().replace("\n", " ")[:72]
        _git(self._repo, "commit", "-m", f"{COMMIT_PREFIX}{summary}")

    async def _discard(self, ref: str) -> None:
        await asyncio.to_thread(_git, self._repo, "reset", "--hard", ref)
        await asyncio.to_thread(_git, self._repo, "clean", "-fd")
