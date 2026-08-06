"""Agentic brain: headless Claude Code sessions.

Two engines behind one `AgentLine` interface, chosen by `claude.engine`:
- "cli" (default): spawn `claude -p` as an argv subprocess and parse stream-json.
- "sdk": drive `ClaudeSDKClient` from the claude-agent-sdk (see claude_sdk.py),
  which adds resume-by-id, mid-session input, interrupt, and per-call gating.

Auth for both comes from the owner's Claude subscription (one-time
`claude setup-token` -> CLAUDE_CODE_OAUTH_TOKEN) — no per-token API billing.
"""

from __future__ import annotations

import asyncio
import json
import shutil
from pathlib import Path
from typing import AsyncIterator, Protocol

from ..config import ClaudeConfig


class AgentLine:
    """One streamed progress item from a running agent session."""

    def __init__(self, kind: str, text: str, *, usage: dict | None = None,
                 cost_usd: float | None = None, session_id: str = "") -> None:
        # "text" | "tool" | "result" | "error" | "session" (session id, once)
        self.kind = kind
        self.text = text
        # set on the result line: the subscription-billed cost the CLI reports
        self.usage = usage
        self.cost_usd = cost_usd
        self.session_id = session_id


def record_usage(ledger, line: "AgentLine", task: str, *,
                 now: float | None = None) -> None:
    """Persist a session's cost to the ledger from its result line. No-op when
    there's no ledger or no cost (e.g. a session that never reached a result)."""
    if ledger is None or line.cost_usd is None:
        return
    usage = line.usage or {}
    ledger.record(
        cost_usd=line.cost_usd,
        task=task,
        session_id=line.session_id,
        input_tokens=int(usage.get("input_tokens", 0)),
        output_tokens=int(usage.get("output_tokens", 0)),
        now=now,
    )


class AgentBridge(Protocol):
    """The shape app.py and selfiterate depend on, regardless of engine."""

    def available(self) -> bool: ...

    def write_settings(self) -> Path | None: ...

    def run(self, prompt: str, workdir: str | Path | None = None,
            system_append: str | None = None, continue_session: bool = False,
            resume: str | None = None) -> AsyncIterator[AgentLine]: ...


def deny_settings(cfg: ClaudeConfig) -> dict:
    """Claude Code settings that deny Read on REMY's secret stores."""
    return {"permissions": {"deny": [f"Read({p})" for p in cfg.deny_read]}}


def settings_path(cfg: ClaudeConfig) -> Path:
    return Path(cfg.agent_settings_file).expanduser()


def write_agent_settings(cfg: ClaudeConfig) -> Path | None:
    """Persist the deny rules to the managed settings file (0600). Idempotent.
    Shared by both engines so the deny-list holds whichever one runs."""
    if not cfg.deny_read:
        return None
    path = settings_path(cfg)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(deny_settings(cfg), indent=2), encoding="utf-8")
    try:
        path.chmod(0o600)
    except OSError:
        pass
    return path


def make_bridge(cfg: ClaudeConfig, ledger=None) -> AgentBridge:
    """Pick the agent engine. Defaults to the raw CLI until the SDK path has
    been validated on-box (ADR 0001). `ledger` (CostLedger) records per-session
    spend for whichever engine runs."""
    if cfg.engine == "sdk":
        from .claude_sdk import ClaudeSDKBridge
        return ClaudeSDKBridge(cfg, ledger=ledger)
    return ClaudeBridge(cfg, ledger=ledger)


class ClaudeBridge:
    """Engine "cli": `claude -p` subprocess, no shell — injection-safe."""

    def __init__(self, cfg: ClaudeConfig, ledger=None) -> None:
        self._cfg = cfg
        self._ledger = ledger
        self._settings_written = False

    def available(self) -> bool:
        return shutil.which(self._cfg.binary) is not None

    def settings_path(self) -> Path:
        return settings_path(self._cfg)

    def write_settings(self) -> Path | None:
        path = write_agent_settings(self._cfg)
        self._settings_written = path is not None
        return path

    def build_cmd(self, prompt: str, system_append: str | None = None,
                  continue_session: bool = False,
                  resume: str | None = None) -> list[str]:
        cmd = [
            self._cfg.binary, "-p", prompt,
            "--output-format", "stream-json", "--verbose",
            "--permission-mode", self._cfg.permission_mode,
            "--allowedTools", self._cfg.allowed_tools,
        ]
        if resume:
            cmd += ["--resume", resume]  # resume a specific session by id
        elif continue_session:
            cmd.append("--continue")  # resume the most recent session in workdir
        if self._cfg.deny_read:
            cmd += ["--settings", str(self.settings_path())]
        if self._cfg.mcp_config:
            cmd += ["--mcp-config", str(Path(self._cfg.mcp_config).expanduser())]
        if system_append:
            cmd += ["--append-system-prompt", system_append]
        return cmd

    async def run(self, prompt: str, workdir: str | Path | None = None,
                  system_append: str | None = None,
                  continue_session: bool = False,
                  resume: str | None = None) -> AsyncIterator[AgentLine]:
        """Run one headless session, yielding progress lines. The final yielded
        line has kind='result' (or 'error')."""
        if not self.available():
            yield AgentLine("error", "claude CLI not installed — run scripts/install.sh")
            return

        cwd = Path(workdir or self._cfg.workdir).expanduser()
        # Make sure the deny-list settings file exists before we hand the agent
        # its Read tool. Once per process; cheap and idempotent.
        if self._cfg.deny_read and not self._settings_written:
            try:
                self.write_settings()
            except OSError:
                pass
        cmd = self.build_cmd(prompt, system_append, continue_session, resume)

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
                    if line.kind in ("result", "error"):
                        record_usage(self._ledger, line, prompt)
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
            usage = msg.get("usage") if isinstance(msg.get("usage"), dict) else None
            cost = msg.get("total_cost_usd")
            sid = str(msg.get("session_id", ""))
            if msg.get("is_error"):
                return AgentLine("error", str(msg.get("result", "unknown error"))[:500],
                                 usage=usage, cost_usd=cost, session_id=sid)
            return AgentLine("result", str(msg.get("result", "")).strip(),
                             usage=usage, cost_usd=cost, session_id=sid)
        return None
