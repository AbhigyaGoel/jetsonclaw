"""The orchestrator: wires mic -> wake -> STT -> router -> skills/brains -> TTS,
publishing everything on the EventBus for the TUI and web dashboard.

`handle_text()` is the single entry point for an utterance — voice, typed TUI
input, dashboard input, and stdin all converge there, so every surface
exercises the identical pipeline.
"""

from __future__ import annotations

import asyncio
import re

import numpy as np

from .audio.capture import CaptureLoop
from .audio.stt import Transcriber
from .audio.tts import Speaker
from .brain.claude import ClaudeBridge
from .brain.memory import ConversationMemory
from .brain.ollama import OllamaBrain
from .config import Config
from .events import EventBus, EventType, State
from .router.intents import Intent, is_affirmation, is_negation, parse
from .skills.loader import SkillLoader
from .skills.selfiterate import SelfIterateSkill
from .skills.spotify import SpotifySkill
from .supervisor import HEALTHY_AFTER_SECS, BootGuard, restart_in_place
from .workspace import Workspace

_WORDISH = re.compile(r"^[A-Za-z!?' ]+$")


class Jarvis:
    def __init__(self, cfg: Config, bus: EventBus, guard: BootGuard,
                 repo_dir: str) -> None:
        self.cfg = cfg
        self.bus = bus
        self.workspace = Workspace()
        self.guard = guard
        self._repo_dir = repo_dir
        self._restart_requested = False
        self._pending: Intent | None = None

        self.memory = ConversationMemory()
        self.ollama = OllamaBrain(cfg.ollama)
        self.claude = ClaudeBridge(cfg.claude)
        self.spotify = SpotifySkill(cfg.spotify)
        self.skills = SkillLoader(self.workspace.skills_dir)
        self.self_iterate = SelfIterateSkill(self.claude, guard, repo_dir, bus)
        self.speaker = Speaker(cfg.tts.voice, cfg.tts.voices_dir,
                               cfg.audio.speaker_device, cfg.tts.length_scale,
                               cfg.tts.enabled)
        self._transcriber: Transcriber | None = None
        self._capture: CaptureLoop | None = None

    # --- lifecycle ---

    async def start(self) -> None:
        loop = asyncio.get_running_loop()
        self.bus.bind_loop(loop)
        self.workspace.ensure()
        self._set_state(State.IDLE, detail="loading models")

        self._transcriber = await asyncio.to_thread(
            Transcriber, self.cfg.stt.model, self.cfg.stt.device,
            self.cfg.stt.compute_type, self.cfg.stt.beam_size, self.cfg.stt.language,
        )
        tts_ok = await asyncio.to_thread(self.speaker.load)
        if self.cfg.tts.enabled and not tts_ok:
            self.bus.publish(EventType.ERROR,
                             message="TTS voice missing — run scripts/install.sh, going text-only")

        self._capture = await asyncio.to_thread(
            CaptureLoop, self.cfg.audio, self.cfg.wake, self.bus, self._on_utterance,
        )
        self._capture.start()
        self._set_state(State.IDLE)
        loop.call_later(HEALTHY_AFTER_SECS, self.guard.mark_healthy)

    def stop(self) -> None:
        if self._capture is not None:
            self._capture.stop()
        self.speaker.stop()
        if self._restart_requested:
            restart_in_place()

    # --- pipeline ---

    def _on_utterance(self, audio: np.ndarray) -> None:
        """Called from the audio thread once a post-wake utterance is captured."""
        loop = self.bus._loop
        if loop is not None:
            asyncio.run_coroutine_threadsafe(self._handle_utterance(audio), loop)

    async def _handle_utterance(self, audio: np.ndarray) -> None:
        self.speaker.stop()  # wake word interrupts any ongoing speech
        self._set_state(State.TRANSCRIBING)
        text = await asyncio.to_thread(self._transcriber.transcribe, audio)
        if not text:
            self.bus.publish(EventType.ERROR, message="no speech detected")
            self._set_state(State.IDLE)
            return
        await self.handle_text(text)

    async def handle_text(self, text: str) -> None:
        """Single entry point for voice, TUI, dashboard, and stdin input."""
        self.bus.publish(EventType.TRANSCRIPT, text=text)
        try:
            await self._route(text)
        except Exception as e:
            self.bus.publish(EventType.ERROR, message=f"{type(e).__name__}: {e}")
            await self._respond("Something broke on my end, sir.")
        finally:
            if self._restart_requested:
                self.stop()
            self._set_state(State.IDLE)

    async def _route(self, text: str) -> None:
        # Confirmation gate for a queued agent task
        if self._pending is not None:
            pending, self._pending = self._pending, None
            if is_affirmation(text):
                await self._execute_agent_intent(pending)
                return
            if is_negation(text):
                await self._respond("Cancelled.")
                return
            # anything else falls through as a fresh command

        intent = parse(text)

        if intent.name == "identity.name":
            await self._respond("Chud")
            return

        if intent.name == "chat.reset":
            self.memory.clear()
            await self._respond("Clean slate.")
            return

        if intent.name.startswith("spotify."):
            if not self.spotify.configured():
                await self._respond("Spotify isn't linked yet.")
                return
            self._set_state(State.THINKING)
            reply = await self.spotify.handle(intent)
            self.bus.publish(EventType.SKILL, skill="spotify", intent=intent.name)
            await self._respond(reply)
            return

        if intent.name == "self.rollback":
            self._set_state(State.WORKING, detail="rollback")
            result = await self.self_iterate.rollback()
            await self._respond(result.message)
            self._restart_requested = result.restart
            return

        if intent.name in ("self.iterate", "agent.task"):
            if self.cfg.claude.confirm_tasks:
                self._pending = intent
                verb = "modify my own code" if intent.name == "self.iterate" \
                    else "run an agent task"
                await self._respond(f"That'll {verb}. Say yes to proceed.")
                return
            await self._execute_agent_intent(intent)
            return

        # Hot-loaded workspace skills (self-grown) — checked before chat
        skill = await asyncio.to_thread(self.skills.find, text)
        if skill is not None:
            self._set_state(State.THINKING, detail=skill.name)
            reply = await asyncio.to_thread(skill.run, text)
            self.bus.publish(EventType.SKILL, skill=skill.name, intent="dynamic")
            await self._respond(reply)
            return

        # Default: local chat with conversation memory, streamed into TTS
        self._set_state(State.THINKING)
        prompt = self.memory.as_prompt(text)
        full = await self._respond_stream(
            self.ollama.stream_sentences(prompt, system=self.workspace.persona_prompt()))
        if full:
            self.memory.add(text, full)

    async def _execute_agent_intent(self, intent: Intent) -> None:
        instruction = intent.slots["instruction"]
        if intent.name == "self.iterate":
            await self._respond("On it. Give me a few minutes.")
            self._set_state(State.WORKING, detail=instruction)
            result = await self.self_iterate.iterate(instruction)
            await self._respond(result.message)
            self._restart_requested = result.restart
            return

        await self._respond("Working on it.")
        self._set_state(State.WORKING, detail=instruction)
        self.bus.publish(EventType.AGENT_START, task=instruction, kind="task")
        result_text = ""
        async for line in self.claude.run(instruction,
                                          system_append=self.workspace.persona_prompt()):
            self.bus.publish(EventType.AGENT_OUTPUT, kind=line.kind, text=line.text)
            if line.kind in ("result", "error"):
                result_text = line.text
        self.bus.publish(EventType.AGENT_DONE, ok=bool(result_text))
        await self._respond(self._summarize_for_voice(result_text))

    # --- output ---

    async def _respond(self, text: str) -> None:
        if not text:
            text = "Done."
        words = text.split()
        block = len(words) <= 2 and bool(_WORDISH.match(text))
        self.bus.publish(EventType.RESPONSE, text=text, block=block)
        if self.speaker.available():
            self._set_state(State.SPEAKING)
            self.bus.publish(EventType.SPEAKING, active=True)
            if self._capture is not None:
                self._capture.pause()  # don't hear ourselves
            try:
                await asyncio.to_thread(self.speaker.speak, text)
            finally:
                if self._capture is not None:
                    self._capture.resume()
                self.bus.publish(EventType.SPEAKING, active=False)

    async def _respond_stream(self, sentences) -> str:
        """Speak sentences as the LLM generates them. Returns the full reply."""
        spoken: list[str] = []
        speaking = False
        try:
            async for sentence in sentences:
                first = not spoken
                spoken.append(sentence)
                self.bus.publish(EventType.RESPONSE, text=sentence, block=False,
                                 partial=not first)
                if self.speaker.available():
                    if not speaking:
                        speaking = True
                        self._set_state(State.SPEAKING)
                        self.bus.publish(EventType.SPEAKING, active=True)
                        if self._capture is not None:
                            self._capture.pause()
                    await asyncio.to_thread(self.speaker.speak, sentence)
        finally:
            if speaking:
                if self._capture is not None:
                    self._capture.resume()
                self.bus.publish(EventType.SPEAKING, active=False)
        return " ".join(spoken)

    @staticmethod
    def _summarize_for_voice(result: str) -> str:
        """Agent results can be long; speak only the first couple of sentences."""
        if not result:
            return "Finished, but the agent had nothing to say."
        sentences = re.split(r"(?<=[.!?])\s+", result.strip())
        return " ".join(sentences[:2])[:300]

    def _set_state(self, state: State, detail: str = "") -> None:
        self.bus.publish(EventType.STATE, state=state.value, detail=detail)
