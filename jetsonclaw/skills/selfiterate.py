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
from dataclasses import dataclass
from pathlib import Path

from ..brain.claude import ClaudeBridge
from ..events import EventBus, EventType
from ..supervisor import BootGuard, _git

COMMIT_PREFIX = "jarvis: "

_AGENT_BRIEF = """You are modifying JetsonClaw, the voice assistant you are running inside of.
Rules:
- Keep changes minimal and focused on the instruction.
- This runs on a Jetson Orin Nano: Python 3.10, numpy<2, no PyAudio (arecord only).
- Do NOT run the app, install packages, or touch git — the harness handles commits and testing.
- After editing, ensure `python3 -m jetsonclaw --selftest` would still pass (it imports every module and runs the unit tests).
"""


@dataclass(frozen=True)
class IterationResult:
    ok: bool
    message: str
    restart: bool = False


class SelfIterateSkill:
    def __init__(self, bridge: ClaudeBridge, guard: BootGuard,
                 repo_dir: str | Path, bus: EventBus) -> None:
        self._bridge = bridge
        self._guard = guard
        self._repo = Path(repo_dir).expanduser()
        self._bus = bus

    async def iterate(self, instruction: str) -> IterationResult:
        if not self._bridge.available():
            return IterationResult(False, "My agentic brain isn't installed yet, sir.")

        before = await asyncio.to_thread(_git, self._repo, "rev-parse", "HEAD")
        self._bus.publish(EventType.AGENT_START, task=instruction, kind="self-iterate")

        async for line in self._bridge.run(instruction, workdir=self._repo,
                                           system_append=_AGENT_BRIEF):
            self._bus.publish(EventType.AGENT_OUTPUT, kind=line.kind, text=line.text)
            if line.kind == "error":
                await self._discard(before)
                return IterationResult(False, f"That didn't work: {line.text[:120]}")

        changed = await asyncio.to_thread(_git, self._repo, "status", "--porcelain")
        if not changed:
            return IterationResult(True, "I looked, but no changes were needed.")

        ok, test_output = await asyncio.to_thread(self._smoke_test)
        if not ok:
            await self._discard(before)
            self._bus.publish(EventType.AGENT_DONE, ok=False, detail=test_output[-800:])
            return IterationResult(False, "The change failed my self-test, so I threw it away.")

        await asyncio.to_thread(self._commit, instruction)
        self._guard.record_good(before)  # the commit we can fall back to
        self._bus.publish(EventType.AGENT_DONE, ok=True, detail="committed, restarting")
        return IterationResult(True, "Done and tested. Restarting with the upgrade.", restart=True)

    async def rollback(self) -> IterationResult:
        last_msg = await asyncio.to_thread(_git, self._repo, "log", "-1", "--format=%s")
        if not last_msg.startswith(COMMIT_PREFIX):
            return IterationResult(False, "The last change wasn't one of mine — not touching it.")
        await asyncio.to_thread(_git, self._repo, "reset", "--hard", "HEAD~1")
        return IterationResult(True, "Reverted my last change. Restarting.", restart=True)

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
