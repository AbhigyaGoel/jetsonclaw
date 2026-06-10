"""LAN web server: serves the dashboard PWA and streams events over /ws.

Open http://<jetson-ip>:8484 from any phone or PC on the network.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse

from ..config import ServerConfig
from ..events import EventBus

STATIC_DIR = Path(__file__).resolve().parent / "static"


def create_app(bus: EventBus) -> FastAPI:
    app = FastAPI(title="JetsonClaw", docs_url=None, redoc_url=None)

    @app.get("/")
    async def index() -> FileResponse:
        return FileResponse(STATIC_DIR / "index.html")

    @app.get("/manifest.json")
    async def manifest() -> FileResponse:
        return FileResponse(STATIC_DIR / "manifest.json")

    @app.websocket("/ws")
    async def ws(socket: WebSocket) -> None:
        await socket.accept()
        queue = bus.subscribe()
        try:
            while True:
                event = await queue.get()
                await socket.send_json(event.to_json())
        except (WebSocketDisconnect, RuntimeError):
            pass
        finally:
            bus.unsubscribe(queue)

    return app


async def serve(bus: EventBus, cfg: ServerConfig) -> None:
    config = uvicorn.Config(create_app(bus), host=cfg.host, port=cfg.port,
                            log_level="warning")
    server = uvicorn.Server(config)
    try:
        await server.serve()
    except asyncio.CancelledError:
        await server.shutdown()
        raise
