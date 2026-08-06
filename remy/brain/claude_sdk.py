"""Engine "sdk": drive Claude through claude-agent-sdk's ClaudeSDKClient.

Same `AgentLine` stream as the CLI engine, so app.py and selfiterate do not
change. What it adds over the CLI (ADR 0001): resume-by-session-id (yielded as an
AgentLine(kind="session") so a job runner can persist it), mid-session input, and
per-call gating — the substrate M3/M5 build on.

The SDK is imported lazily inside methods so this module loads even when the
package is absent (the CLI stays the default until the SDK path is validated
on-box). Auth is the same subscription token; the SDK subprocess inherits the
environment, so CLAUDE_CODE_OAUTH_TOKEN passes through unchanged.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import AsyncIterator

from ..config import ClaudeConfig
from .claude import AgentLine, settings_path, write_agent_settings


def _sdk_available() -> bool:
    try:
        import claude_agent_sdk  # noqa: F401
    except Exception:
        return False
    return True


class ClaudeSDKBridge:
    def __init__(self, cfg: ClaudeConfig) -> None:
        self._cfg = cfg
        self._settings_written = False

    def available(self) -> bool:
        # The wheel bundles the CLI binary, so importability is the only gate.
        return _sdk_available()

    def settings_path(self) -> Path:
        return settings_path(self._cfg)

    def write_settings(self) -> Path | None:
        path = write_agent_settings(self._cfg)
        self._settings_written = path is not None
        return path

    def _option_kwargs(self, workdir: str | Path | None, system_append: str | None,
                       continue_session: bool, resume: str | None) -> dict:
        """Build ClaudeAgentOptions kwargs. Pure — no SDK import — so the mapping
        is unit-testable off-box."""
        kw: dict = {
            "cwd": str(Path(workdir or self._cfg.workdir).expanduser()),
            "allowed_tools": [t.strip() for t in self._cfg.allowed_tools.split(",")
                              if t.strip()],
            "permission_mode": self._cfg.permission_mode,
        }
        if system_append:
            # Append to Claude Code's preset prompt, never replace it.
            kw["system_prompt"] = {"type": "preset", "preset": "claude_code",
                                   "append": system_append}
        if resume:
            kw["resume"] = resume  # resume a specific session by id
        elif continue_session:
            kw["continue_conversation"] = True
        if self._cfg.deny_read:
            kw["settings"] = str(self.settings_path())
        if self._cfg.mcp_config:
            servers = _load_mcp_servers(self._cfg.mcp_config)
            if servers:
                kw["mcp_servers"] = servers
        return kw

    async def run(self, prompt: str, workdir: str | Path | None = None,
                  system_append: str | None = None,
                  continue_session: bool = False,
                  resume: str | None = None) -> AsyncIterator[AgentLine]:
        if not self.available():
            yield AgentLine("error",
                            "claude-agent-sdk not installed — pip install claude-agent-sdk")
            return

        from claude_agent_sdk import (  # deferred: absent off-box
            AssistantMessage, ClaudeAgentOptions, ClaudeSDKClient, ResultMessage,
            TextBlock, ToolUseBlock,
        )

        if self._cfg.deny_read and not self._settings_written:
            try:
                self.write_settings()
            except OSError:
                pass

        options = ClaudeAgentOptions(**self._option_kwargs(
            workdir, system_append, continue_session, resume))
        session_seen = False
        got_result = False
        try:
            async with ClaudeSDKClient(options=options) as client:
                await client.query(prompt)
                # Surface the session id early so a job runner can persist it
                # before the (possibly long) session finishes.
                sid = await _early_session_id(client)
                if sid:
                    session_seen = True
                    yield AgentLine("session", sid)
                # Per-message inactivity timeout (parity with the CLI engine's
                # per-line timeout). asyncio.timeout() is 3.11+, so we wrap each
                # __anext__ instead — Jetson is on 3.10. Exhaustion raises
                # StopAsyncIteration cleanly through wait_for (PEP 479 wraps
                # StopIteration, not StopAsyncIteration; verified).
                stream = client.receive_response().__aiter__()
                while True:
                    try:
                        msg = await asyncio.wait_for(stream.__anext__(),
                                                     timeout=self._cfg.timeout_secs)
                    except StopAsyncIteration:
                        break
                    except asyncio.TimeoutError:
                        try:
                            await client.interrupt()
                        except Exception:
                            pass
                        yield AgentLine("error",
                                        f"agent idle >{self._cfg.timeout_secs:.0f}s")
                        return
                    for line in self._map(msg, AssistantMessage, TextBlock,
                                          ToolUseBlock, ResultMessage):
                        if line.kind == "session":
                            if session_seen:
                                continue
                            session_seen = True
                        if line.kind == "result":
                            got_result = True
                        yield line
        except Exception as e:
            yield AgentLine("error", f"agent crashed: {e}")
            return

        if not got_result:
            yield AgentLine("error", "agent produced no result")

    @staticmethod
    def _map(msg, AssistantMessage, TextBlock, ToolUseBlock,
             ResultMessage) -> list[AgentLine]:
        """Map one SDK message to AgentLines. Classes are injected so this is
        testable with stand-ins when the SDK isn't installed."""
        lines: list[AgentLine] = []
        if isinstance(msg, AssistantMessage):
            texts, tools = [], []
            for block in msg.content:
                if isinstance(block, TextBlock) and block.text.strip():
                    texts.append(block.text.strip())
                elif isinstance(block, ToolUseBlock):
                    tools.append(block.name)
            if tools:
                lines.append(AgentLine("tool", ", ".join(tools)))
            if texts:
                lines.append(AgentLine("text", " ".join(texts)))
        elif isinstance(msg, ResultMessage):
            sid = getattr(msg, "session_id", "") or ""
            if sid:
                lines.append(AgentLine("session", sid))
            if getattr(msg, "is_error", False):
                lines.append(AgentLine(
                    "error", str(getattr(msg, "result", "") or "unknown error")[:500]))
            else:
                lines.append(AgentLine(
                    "result", str(getattr(msg, "result", "") or "").strip()))
        return lines


async def _early_session_id(client) -> str:
    """Best-effort: pull the session id from server info right after connect."""
    try:
        info = await client.get_server_info()
    except Exception:
        return ""
    if isinstance(info, dict):
        return str(info.get("session_id", "") or "")
    return ""


def _load_mcp_servers(mcp_config: str) -> dict:
    """Read an MCP servers json file into the dict the SDK expects. Best-effort;
    M5 owns real capability composition."""
    try:
        data = json.loads(Path(mcp_config).expanduser().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    servers = data.get("mcpServers", data)
    return servers if isinstance(servers, dict) else {}
