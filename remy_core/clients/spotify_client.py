"""The Spotify backend seam.

Providers/Synthesizers read through this interface, never the Web API
directly, so they're testable here (FakeSpotifyClient serves a baked
catalog) and identical on the Jetson (a real adapter wraps REMY's Spotify
creds, which it already holds for playback).

Real adapter note, `top_tracks(time_range, limit)` maps onto
`GET /v1/me/top/tracks?time_range={short|medium|long}_term&limit={limit}`.
That endpoint returns tracks already ordered by the user's affinity but
carries NO play counts, so a real adapter sets `plays=None` and the display
falls back to listening rank. The fake supplies plays for a richer demo.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Protocol

# Spotify's affinity windows. "past three months" ≈ medium.
TIME_RANGES = ("short", "medium", "long")   # ~4wk, ~6mo, ~all-time


@dataclass(frozen=True)
class Track:
    name: str
    artist: str
    rank: int                       # 1-based position in the user's top list
    plays: Optional[int] = None     # real count if the source has one, else None


class SpotifyClient(Protocol):
    def top_tracks(self, time_range: str, limit: int) -> list[Track]:
        """The user's top tracks over an affinity window, ordered by affinity."""

    def create_playlist(self, name: str, track_names: list[str]) -> dict:
        """Create a playlist and add the named tracks. Returns id + url."""

    def play(self, track_names: list[str]) -> dict:
        """Start playback of the given tracks."""


# A baked top-tracks list (medium_term-ish) with a healthy dose of Ye, so the
# favorite-artist synthesizer has real-looking data to rank.
_CATALOG = [
    ("Runaway", "Kanye West", 512),
    ("Blinding Lights", "The Weeknd", 498),
    ("Stronger", "Kanye West", 441),
    ("One Dance", "Drake", 405),
    ("Power", "Kanye West", 388),
    ("Flashing Lights", "Kanye West", 351),
    ("Levitating", "Dua Lipa", 322),
    ("Gold Digger", "Kanye West", 300),
    ("bad guy", "Billie Eilish", 271),
    ("Bound 2", "Kanye West", 240),
    ("Sunflower", "Post Malone", 233),
    ("Heartless", "Kanye West", 205),
]


class FakeSpotifyClient:
    """Serves the baked catalog and records writes. `time_range` is accepted
    but not varied. `playlists` and `played` let tests assert effects.

    Real adapter mapping (behind REMY's Spotify creds on the Jetson):
      create_playlist → POST /v1/users/{id}/playlists then POST .../tracks
      play            → PUT  /v1/me/player/play
    """

    def __init__(self) -> None:
        self.playlists: list[dict] = []
        self.played: list[list[str]] = []

    def top_tracks(self, time_range: str, limit: int) -> list[Track]:
        if time_range not in TIME_RANGES:
            raise ValueError(f"time_range must be one of {TIME_RANGES}, got {time_range!r}")
        return [
            Track(name=n, artist=a, rank=i + 1, plays=p)
            for i, (n, a, p) in enumerate(_CATALOG[:limit])
        ]

    def create_playlist(self, name: str, track_names: list[str]) -> dict:
        self.playlists.append({"name": name, "tracks": list(track_names)})
        n = len(self.playlists)
        return {"id": f"pl_fake_{n}", "url": f"https://open.spotify.com/playlist/fake{n}", "name": name}

    def play(self, track_names: list[str]) -> dict:
        self.played.append(list(track_names))
        return {"playing": True, "count": len(track_names)}
