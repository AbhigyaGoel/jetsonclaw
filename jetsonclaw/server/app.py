"""LAN web server: serves the dashboard PWA and streams events over /ws.
The socket is bidirectional — clients can send {"type": "say", "text": ...}
to issue commands, which run through the exact same pipeline as voice.

Open http://<jetson-ip>:8484 from any phone or PC on the network. Set
server.auth_token in config to require ?key=<token>.
"""

from __future__ import annotations

import asyncio
import hmac
from pathlib import Path
from typing import Awaitable, Callable

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, PlainTextResponse

from ..config import ServerConfig
from ..events import EventBus

STATIC_DIR = Path(__file__).resolve().parent / "static"
MAX_TEXT_LEN = 500

OnText = Callable[[str], Awaitable[None]]


def create_app(bus: EventBus, cfg: ServerConfig,
               on_text: OnText | None = None) -> FastAPI:
    app = FastAPI(title="JetsonClaw", docs_url=None, redoc_url=None)

    def authorized(key: str | None) -> bool:
        if not cfg.auth_token:
            return True
        return key is not None and hmac.compare_digest(key, cfg.auth_token)

    @app.get("/")
    async def index(key: str | None = None):
        if not authorized(key):
            return PlainTextResponse("unauthorized — append ?key=<token>", status_code=401)
        return FileResponse(STATIC_DIR / "index.html")

    @app.get("/manifest.json")
    async def manifest() -> FileResponse:
        return FileResponse(STATIC_DIR / "manifest.json")

    @app.websocket("/ws")
    async def ws(socket: WebSocket) -> None:
        if not authorized(socket.query_params.get("key")):
            await socket.close(code=4401)
            return
        await socket.accept()
        queue = bus.subscribe()

        async def sender() -> None:
            while True:
                event = await queue.get()
                await socket.send_json(event.to_json())

        async def receiver() -> None:
            while True:
                msg = await socket.receive_json()
                if msg.get("type") == "say" and on_text is not None:
                    text = str(msg.get("text", "")).strip()[:MAX_TEXT_LEN]
                    if text:
                        asyncio.ensure_future(on_text(text))

        send_task = asyncio.create_task(sender())
        try:
            await receiver()
        except (WebSocketDisconnect, RuntimeError, ValueError):
            pass
        finally:
            send_task.cancel()
            bus.unsubscribe(queue)

    return app


async def serve(bus: EventBus, cfg: ServerConfig,
                on_text: OnText | None = None) -> None:
    config = uvicorn.Config(create_app(bus, cfg, on_text), host=cfg.host,
                            port=cfg.port, log_level="warning")
    server = uvicorn.Server(config)
    try:
        await server.serve()
    except asyncio.CancelledError:
        await server.shutdown()
        raise
