"""Textual TUI — the on-device face of JARVIS. Pure EventBus subscriber."""

from __future__ import annotations

import asyncio

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Input, RichLog, Static

from ..app import Jarvis
from ..events import EventBus, EventType
from .blockfont import render_block

VU_WIDTH = 40
VU_MAX_RMS = 3000.0

_STATE_WORDS = {
    "idle": "READY",
    "listening": "LISTEN",
    "transcribing": "HMM",
    "thinking": "HMM",
    "working": "WORKING",
    "speaking": None,  # filled with the assistant's name at runtime
}


class JarvisTUI(App):
    TITLE = "REMY"
    BINDINGS = [("ctrl+q", "quit", "Quit")]
    CSS = """
    #status { height: 8; content-align: center middle; color: cyan; }
    #vu { height: 1; color: green; }
    #detail { height: 1; color: #7a8a94; }
    #convo { border: round cyan; height: 1fr; }
    #agent { border: round magenta; height: 1fr; }
    #cmdline { border: round #2a4a5a; }
    """

    def __init__(self, jarvis: Jarvis, bus: EventBus) -> None:
        super().__init__()
        self._jarvis = jarvis
        self._bus = bus
        self._name = jarvis.cfg.identity.name

    def compose(self) -> ComposeResult:
        yield Static(render_block("BOOT"), id="status")
        yield Static("", id="vu")
        yield Static("loading models...", id="detail")
        with Horizontal():
            with Vertical():
                yield RichLog(id="convo", wrap=True, markup=False, highlight=False)
            with Vertical():
                yield RichLog(id="agent", wrap=True, markup=False, highlight=False)
        yield Input(placeholder="say 'hey jarvis' — or type a command (ctrl+q quits)",
                    id="cmdline")

    async def on_mount(self) -> None:
        self.run_worker(self._pump(), exclusive=False)
        self.run_worker(self._boot(), exclusive=False)

    async def _boot(self) -> None:
        try:
            await self._jarvis.start()
        except Exception as e:
            self.query_one("#detail", Static).update(f"BOOT FAILED: {e}")

    async def _pump(self) -> None:
        queue = self._bus.subscribe()
        convo = self.query_one("#convo", RichLog)
        agent = self.query_one("#agent", RichLog)
        status = self.query_one("#status", Static)
        vu = self.query_one("#vu", Static)
        detail = self.query_one("#detail", Static)

        while True:
            ev = await queue.get()
            if ev.type == EventType.STATE:
                word = _STATE_WORDS.get(ev.data.get("state", ""), "READY") \
                    or self._name.upper()
                status.update(render_block(word))
                detail.update(ev.data.get("detail", ""))
            elif ev.type == EventType.AUDIO_LEVEL:
                filled = min(VU_WIDTH, int(ev.data.get("rms", 0) / VU_MAX_RMS * VU_WIDTH))
                vu.update(" " + "█" * filled + "░" * (VU_WIDTH - filled))
            elif ev.type == EventType.WAKE:
                convo.write(f"[wake {ev.data.get('score', 0):.2f}]")
                status.update(render_block("YES?"))
            elif ev.type == EventType.TRANSCRIPT:
                convo.write(f"\n» you: {ev.data.get('text', '')}")
            elif ev.type == EventType.RESPONSE:
                text = ev.data.get("text", "")
                if ev.data.get("block"):
                    convo.write("\n" + render_block(text))
                elif ev.data.get("partial"):
                    convo.write(f"          {text}")  # streamed continuation
                else:
                    convo.write(f"« {self._name.lower()}: {text}")
            elif ev.type == EventType.AGENT_START:
                agent.write(f"\n▶ {ev.data.get('kind', 'task')}: {ev.data.get('task', '')}")
            elif ev.type == EventType.AGENT_OUTPUT:
                kind = ev.data.get("kind", "")
                prefix = {"tool": "  ⚙ ", "text": "  · ", "result": "  ✔ ",
                          "error": "  ✘ "}.get(kind, "  ")
                agent.write(prefix + ev.data.get("text", "")[:200])
            elif ev.type == EventType.AGENT_DONE:
                agent.write("  ✔ done" if ev.data.get("ok") else "  ✘ failed")
            elif ev.type == EventType.ERROR:
                convo.write(f"  ! {ev.data.get('message', '')}")

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        text = event.value.strip()
        event.input.value = ""
        if text:
            asyncio.create_task(self._jarvis.handle_text(text))

    def action_quit(self) -> None:
        self._jarvis.stop()
        self.exit()
