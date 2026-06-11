"""Intent parsing — pure functions, no I/O, fully unit-testable.

The router decides three tiers from one transcript:
  fast skill (Spotify, name)  ->  local LLM chat (ollama)  ->  agent (Claude Code)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Intent:
    name: str
    slots: dict[str, str] = field(default_factory=dict)


# Phrases that mean "JARVIS, modify your own code"
_SELF_ITERATE = re.compile(
    r"\b(upgrade|improve|update|modify|fix|rewrite|teach|give)\s+(yourself|your\s+(own\s+)?"
    r"(code|skills?|voice|ui|interface|brain|abilities|response|personality))\b"
)
_ROLLBACK = re.compile(r"\b(undo|revert|roll\s*back)\b.*\b(that|it|change|update|last)?\b")

# Complex commands that need the agentic brain, not a 3B chat model
_AGENT_VERBS = re.compile(
    r"^\s*(edit|create|build|write|deploy|refactor|debug|implement|update|fix)\s+(the|my|a|an)\b"
)

_NOW_PLAYING = re.compile(
    r"(what'?s\s+playing|what\s+song|what\s+track|now\s+playing|currently\s+playing)"
)
_PLAYLIST = re.compile(
    r"^play\s+(?:my\s+)?(?:playlist\s+(?P<a>.+)|(?P<b>.+?)\s+(?:from\s+my\s+)?playlist)\s*$"
)
_PLAY_TRACK = re.compile(r"^play\s+(?P<q>.+)$")
_RESUME_WORDS = {"", "music", "it", "song", "the music", "the song", "spotify"}


_YES = re.compile(r"^(yes|yeah|yep|sure|go ahead|do it|proceed|confirm|affirmative|please do)\b")
_NO = re.compile(r"^(no|nope|nah|cancel|stop|don't|never mind|nevermind|negative|abort)\b")


def is_affirmation(raw: str) -> bool:
    return bool(_YES.match(_clean(raw)))


def is_negation(raw: str) -> bool:
    return bool(_NO.match(_clean(raw)))


def _clean(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[.,;:!?]+$", "", text)
    text = re.sub(r"^(hey\s+)?(jarvis|remy)[,\s]*", "", text)
    return text.strip()


def parse(raw: str) -> Intent:
    text = _clean(raw)

    if _ROLLBACK.search(text) and any(w in text for w in ("undo", "revert", "roll")):
        return Intent("self.rollback")
    if _SELF_ITERATE.search(text):
        return Intent("self.iterate", {"instruction": raw.strip()})

    if "your name" in text or re.fullmatch(r"who are you", text):
        return Intent("identity.self")
    if ("name" in text and any(w in text for w in ("my", "who", "what"))) \
            or re.fullmatch(r"who\s+am\s+i", text):
        return Intent("identity.name")

    if re.fullmatch(r"(forget (that|it|everything)|new (topic|conversation)|clean slate)", text):
        return Intent("chat.reset")

    remember = re.match(r"^remember\s+(that\s+)?(?P<fact>.{3,})$", text)
    if remember:
        return Intent("memory.remember", {"fact": remember.group("fact").strip()})

    recall = re.match(r"^(what|anything) do you (remember|know)\s+(about\s+)?(?P<q>.+)$", text)
    if recall:
        return Intent("memory.recall", {"query": recall.group("q").strip()})

    if re.fullmatch(r"(status( report)?|system status|diagnostics|sitrep)", text):
        return Intent("system.status")

    if _NOW_PLAYING.search(text):
        return Intent("spotify.now_playing")
    if re.search(r"\b(skip|next)\b", text):
        return Intent("spotify.next")
    if re.search(r"\b(pause|stop)\b", text):
        return Intent("spotify.pause")
    if re.match(r"^resume\b", text):
        return Intent("spotify.resume")

    playlist = _PLAYLIST.match(text)
    if playlist:
        name = (playlist.group("a") or playlist.group("b") or "").strip()
        if name and name not in _RESUME_WORDS:
            return Intent("spotify.play_playlist", {"name": name})

    track = _PLAY_TRACK.match(text)
    if track:
        query = track.group("q").strip()
        if query in _RESUME_WORDS:
            return Intent("spotify.resume")
        return Intent("spotify.play_track", {"query": query})
    if text in ("play",):
        return Intent("spotify.resume")

    if _AGENT_VERBS.match(text):
        return Intent("agent.task", {"instruction": raw.strip()})

    return Intent("chat", {"text": raw.strip()})
