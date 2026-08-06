"""The route table: how an utterance maps to a capability + its params.

Each Route has a matcher that returns a params dict on a hit (or None to
pass). The router tries them in order, most specific first, so "favorite
Kanye songs" (Judge) is tested before the general "top tracks" (Tell).

This is the deterministic, local fast-path. On the Jetson, an utterance that
matches nothing here is where REMY would hand off to the local qwen model to
classify; that fallback lives above this table, not in it.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable, Optional

from ..actions import ACTIONS
from ..chains import CHAINS
from ..context import RemyContext
from ..parse.datetime_parse import TimeParseError, parse_datetime
from ..providers import PROVIDERS
from ..synthesizers import SYNTHESIZERS


@dataclass(frozen=True)
class Route:
    verb: str                    # "tell" | "judge" | "act"
    method: str                  # "fetch" | "derive" | "" (actions self-parse)
    client_key: Optional[str]    # which backend client this needs
    capability: object
    match: Callable[[str, RemyContext], Optional[dict]]


# --- shared param extractors -------------------------------------------------

def _window(text: str) -> str:
    """Spoken time window → Spotify affinity range."""

    t = text.lower()
    if re.search(r"all[-\s]?time|of all time|\bever\b|overall", t):
        return "long"
    if re.search(r"this week|lately|recently|these days|this month|last month|past month\b", t):
        return "short"
    return "medium"     # "past few/three months", "this quarter", default


def _limit(text: str, default: int = 5) -> int:
    if m := re.search(r"\btop\s+(\d{1,2})\b", text.lower()):
        return int(m.group(1))
    return default


# --- matchers ----------------------------------------------------------------

_ADD_VERB = re.compile(
    r"^\s*(?:hey\s+remy[,\s]*)?(?:can you\s+|please\s+)?"
    r"(?:add|schedule|put|book|create|set up|set|remind me to)\b",
    re.IGNORECASE,
)
_FAV = re.compile(
    r"(?:favou?rite|best|top|most[-\s]?played)\s+(.+?)\s+(?:songs?|tracks?|music|hits?)",
    re.IGNORECASE,
)
_TOP = re.compile(
    r"top tracks|top songs|most[-\s]?listened|most[-\s]?played|on repeat|"
    r"been listening|listening to (?:lately|recently)|what.*listening",
    re.IGNORECASE,
)


_PLAYLIST = re.compile(r"\b(?:make|build|create|start)\s+(?:me\s+)?a\s+playlist\b", re.IGNORECASE)
_PLAYLIST_OF = re.compile(
    r"playlist\s+(?:of|from|with|out of)\s+(?:my\s+)?"
    r"(?:favou?rite\s+|top\s+|most[-\s]?played\s+)?"
    r"(.+?)(?:\s+songs?|\s+tracks?|\s+music)?(?:\s+(?:and|then)\b.*|\s+called\b.*)?$",
    re.IGNORECASE,
)


def _match_playlist_chain(utterance: str, ctx: RemyContext) -> Optional[dict]:
    if not _PLAYLIST.search(utterance):
        return None
    m = _PLAYLIST_OF.search(utterance)
    if not m:
        return None
    artist = re.sub(r"^\d+\s+", "", m.group(1).strip())
    if not artist:
        return None
    play = bool(re.search(r"\b(?:and|then)\s+(?:play|start)\b|\bplay it\b|\bstart it\b", utterance, re.IGNORECASE))
    return {"artist": artist, "artist_display": artist.title(), "play": play, "limit": _limit(utterance, 10)}


def _match_favorite(utterance: str, ctx: RemyContext) -> Optional[dict]:
    m = _FAV.search(utterance)
    if not m:
        return None
    artist = re.sub(r"^(?:my|the)\s+", "", m.group(1).strip(), flags=re.IGNORECASE)
    artist = re.sub(r"^\d+\s+", "", artist).strip()      # drop "5" from "top 5 kanye"
    if not artist:
        return None
    return {"artist": artist, "artist_display": artist.title(), "limit": _limit(utterance)}


def _match_top(utterance: str, ctx: RemyContext) -> Optional[dict]:
    if not _TOP.search(utterance):
        return None
    return {"window": _window(utterance), "limit": _limit(utterance)}


def _match_calendar(utterance: str, ctx: RemyContext) -> Optional[dict]:
    if not _ADD_VERB.search(utterance):
        return None
    try:
        parse_datetime(utterance, ctx.now)    # only an event if there's a when
    except TimeParseError:
        return None
    return {}      # the Action parses its own params from the utterance


# Order matters: most specific first. The playlist chain contains the words
# "favorite <artist> songs", so it must be tested before the plain Judge rule.
ROUTES: list[Route] = [
    Route("chain", "gather", None, CHAINS["chain.playlist_from_artist"], _match_playlist_chain),
    Route("judge", "derive", "spotify", SYNTHESIZERS["spotify.favorite_by_artist"], _match_favorite),
    Route("tell", "fetch", "spotify", PROVIDERS["spotify.top_tracks"], _match_top),
    Route("act", "", "calendar", ACTIONS["calendar.add"], _match_calendar),
]
