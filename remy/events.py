"""Async event bus. Every component publishes immutable events; TUI, web UI,
and logs are all just subscribers. This is the spine of the whole app."""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class EventType(str, Enum):
    STATE = "state"            # pipeline state changed
    AUDIO_LEVEL = "audio_level"  # mic RMS, for waveform UIs
    WAKE = "wake"              # wake word detected
    TRANSCRIPT = "transcript"  # user speech transcribed
    RESPONSE = "response"      # JARVIS replied (text)
    AGENT_START = "agent_start"    # claude session began
    AGENT_OUTPUT = "agent_output"  # streamed agent progress line
    AGENT_DONE = "agent_done"
    SKILL = "skill"            # a skill handled the command
    ERROR = "error"
    SPEAKING = "speaking"      # TTS started/stopped


class State(str, Enum):
    IDLE = "idle"
    LISTENING = "listening"
    TRANSCRIBING = "transcribing"
    THINKING = "thinking"
    WORKING = "working"  # long-running agent task
    SPEAKING = "speaking"


@dataclass(frozen=True)
class Event:
    type: EventType
    data: dict[str, Any] = field(default_factory=dict)
    ts: float = field(default_factory=time.time)

    def to_json(self) -> dict[str, Any]:
        return {"type": self.type.value, "data": self.data, "ts": self.ts}


class EventBus:
    """Fan-out pub/sub on asyncio queues. Thread-safe publish via publish_threadsafe."""

    def __init__(self, loop: asyncio.AbstractEventLoop | None = None) -> None:
        self._subscribers: list[asyncio.Queue[Event]] = []
        self._loop = loop

    def bind_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop

    @property
    def loop(self) -> asyncio.AbstractEventLoop | None:
        return self._loop

    def subscribe(self, maxsize: int = 256) -> asyncio.Queue[Event]:
        queue: asyncio.Queue[Event] = asyncio.Queue(maxsize=maxsize)
        self._subscribers.append(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue[Event]) -> None:
        if queue in self._subscribers:
            self._subscribers.remove(queue)

    def publish(self, type: EventType, **data: Any) -> None:
        event = Event(type=type, data=data)
        for queue in list(self._subscribers):
            try:
                queue.put_nowait(event)
            except asyncio.QueueFull:
                # Drop oldest so slow consumers (e.g. a stalled websocket)
                # never block the voice pipeline.
                try:
                    queue.get_nowait()
                    queue.put_nowait(event)
                except (asyncio.QueueEmpty, asyncio.QueueFull):
                    pass

    def publish_threadsafe(self, type: EventType, **data: Any) -> None:
        """Publish from a non-asyncio thread (the audio capture thread)."""
        if self._loop is None:
            raise RuntimeError("EventBus loop not bound; call bind_loop() first")
        self._loop.call_soon_threadsafe(lambda: self.publish(type, **data))
