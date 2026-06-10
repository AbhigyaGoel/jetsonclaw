"""Launchers: TUI mode (default) and headless console mode. Both also start
the LAN web server."""

from __future__ import annotations

import asyncio
from pathlib import Path

from .app import Jarvis
from .config import Config
from .events import EventBus, EventType
from .server.app import serve
from .supervisor import BootGuard


def run_tui(cfg: Config, guard: BootGuard, repo_dir: Path) -> int:
    from .tui.app import JarvisTUI

    bus = EventBus()
    jarvis = Jarvis(cfg, bus, guard, str(repo_dir))
    tui = JarvisTUI(jarvis, bus)

    async def _with_server() -> None:
        server_task = asyncio.create_task(serve(bus, cfg.server))
        try:
            await tui.run_async()
        finally:
            server_task.cancel()

    asyncio.run(_with_server())
    return 0


def run_headless(cfg: Config, guard: BootGuard, repo_dir: Path) -> int:
    from .tui.blockfont import render_block

    bus = EventBus()
    jarvis = Jarvis(cfg, bus, guard, str(repo_dir))

    async def _print_events() -> None:
        queue = bus.subscribe()
        while True:
            ev = await queue.get()
            if ev.type == EventType.AUDIO_LEVEL:
                continue  # too chatty for a console
            if ev.type == EventType.TRANSCRIPT:
                print(f'\n» you: "{ev.data.get("text", "")}"')
            elif ev.type == EventType.RESPONSE:
                text = ev.data.get("text", "")
                print(render_block(text) if ev.data.get("block") else f"« jarvis: {text}")
            elif ev.type == EventType.WAKE:
                print("[wake word detected]")
            elif ev.type == EventType.STATE:
                detail = ev.data.get("detail", "")
                print(f"  ({ev.data.get('state')}{': ' + detail if detail else ''})")
            elif ev.type == EventType.AGENT_OUTPUT:
                print(f"  agent {ev.data.get('kind')}: {ev.data.get('text', '')[:160]}")
            elif ev.type == EventType.ERROR:
                print(f"  ! {ev.data.get('message', '')}")

    async def _main() -> None:
        printer = asyncio.create_task(_print_events())
        server_task = asyncio.create_task(serve(bus, cfg.server))
        await jarvis.start()
        print("\nReady. Say 'hey jarvis'. Ctrl-C to quit.\n")
        try:
            await asyncio.Event().wait()  # run until interrupted
        finally:
            printer.cancel()
            server_task.cancel()

    try:
        asyncio.run(_main())
    except KeyboardInterrupt:
        print("\nShutting down.")
    finally:
        jarvis.stop()
    return 0
