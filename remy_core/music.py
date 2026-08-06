"""Music helpers shared by the Spotify Provider and Synthesizer.

Turns a list of Tracks into a remy_ui Ranking (draw) and a spoken line
(say). Kept in one place so the Tell path and the Judge path shape and
phrase results identically.
"""

from __future__ import annotations

from typing import Sequence

from remy_ui import Entry, Ranking

from .clients.spotify_client import Track
from .phrase import natural_list


def ranking_from_tracks(title: str, tracks: Sequence[Track], caption: str) -> Ranking:
    """Build a remy_ui Ranking. Uses real play counts when present, else the
    listening-rank as the magnitude (so the bars still taper honestly)."""

    n = len(tracks)
    have_plays = all(t.plays is not None for t in tracks)
    entries = tuple(
        Entry(t.name, t.plays if have_plays else (n - i))
        for i, t in enumerate(tracks)
    )
    return Ranking(title=title, items=entries, top=n, caption=caption)


def tracks_speech(prefix: str, tracks: Sequence[Track]) -> str:
    """A natural spoken summary: '<prefix>: A, B, and C.'"""

    names = [t.name for t in tracks]
    return f"{prefix}: {natural_list(names)}."
