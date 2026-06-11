"""Agentic brain: headless Claude Code CLI sessions.

Runs `claude -p` as an argv subprocess (no shell — injection-safe) with
stream-json output so the UI can show live progress. Auth comes from the
user's Claude subscription (one-time `claude setup-token` ->
CLAUDE_CODE_OAUTH_TOKEN) — no per-token API billing.
"""

from __future__ import annotations

import asyncio
import json
import shutil
from pathlib import Path
from typing import AsyncIterator

from ..config import ClaudeConfig


class AgentLine:
    """One streamed progress item from a running agent session."""

    def __init__(self, kind: str, text: str) -> None:
        self.kind = kind  # "text" | "tool" | "result" | "error"
        self.text = text


class ClaudeBridge:
    def __init__(self, cfg: ClaudeConfig) -> None:
        self._cfg = cfg

    def available(self) -> bool:
        return shutil.which(self._cfg.binary) is not None

    async def run(self, prompt: str, workdir: str | Path | None = None,
                  system_append: str | None = None) -> AsyncIterator[AgentLine]:
        """Run one headless session, yielding progress lines. The final yielded
        line has kind='result' (or 'error')."""
        if not self.available():
            yield AgentLine("error", "claude CLI not installed — run scripts/install.sh")
            return

        cwd = Path(workdir or self._cfg.workdir).expanduser()
        cmd = [
            self._cfg.binary, "-p", prompt,
            "--output-format", "stream-json", "--verbose",
            "--permission-mode", self._cfg.permission_mode,
            "--allowedTools", self._cfg.allowed_tools,
        ]
        if system_append:
            cmd += ["--append-system-prompt", system_append]

        proc = await asyncio.create_subprocess_exec(
            *cmd, cwd=str(cwd),
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
        )
        got_result = False
        try:
            assert proc.stdout is not None
            while True:
                raw = await asyncio.wait_for(proc.stdout.readline(),
                                             timeout=self._cfg.timeout_secs)
                if not raw:
                    break
                line = self._parse(raw)
                if line is not None:
                    if line.kind == "result":
                        got_result = True
                    yield line
            await proc.wait()
        except asyncio.TimeoutError:
            proc.kill()
            yield AgentLine("error", f"agent timed out after {self._cfg.timeout_secs:.0f}s")
            return
        except Exception as e:
            proc.kill()
            yield AgentLine("error", f"agent crashed: {e}")
            return

        if not got_result:
            stderr = b""
            if proc.stderr is not None:
                stderr = await proc.stderr.read()
            yield AgentLine("error",
                            f"agent exited ({proc.returncode}): {stderr.decode()[:500]}")

    @staticmethod
    def _parse(raw: bytes) -> AgentLine | None:
        try:
            msg = json.loads(raw.decode())
        except (json.JSONDecodeError, UnicodeDecodeError):
            return None
        kind = msg.get("type")
        if kind == "assistant":
            parts = msg.get("message", {}).get("content", [])
            texts, tools = [], []
            for part in parts:
                if part.get("type") == "text" and part.get("text", "").strip():
                    texts.append(part["text"].strip())
                elif part.get("type") == "tool_use":
                    tools.append(part.get("name", "tool"))
            if tools:
                return AgentLine("tool", ", ".join(tools))
            if texts:
                return AgentLine("text", " ".join(texts))
        elif kind == "result":
            if msg.get("is_error"):
                return AgentLine("error", str(msg.get("result", "unknown error"))[:500])
            return AgentLine("result", str(msg.get("result", "")).strip())
        return None
