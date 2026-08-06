"""Provider: the user's top tracks. The Tell verb for music.

"my most-listened in the past three months" → medium_term top tracks →
a Ranking that renders and speaks. Pure read, no judgment: it reports what
Spotify's affinity ranking already says.
"""

from __future__ import annotations

from typing import Any

from ..capability import Presentation
from ..context import RemyContext
from ..music import ranking_from_tracks, tracks_speech

# How spoken time windows map to Spotify affinity ranges.
_WINDOW = {
    "short": ("this month", "short"),
    "medium": ("the past few months", "medium"),
    "long": ("all time", "long"),
}


class SpotifyTopTracks:
    name = "spotify.top_tracks"

    def fetch(self, params: dict, ctx: RemyContext, client: Any) -> Presentation:
        window = params.get("window", "medium")
        limit = int(params.get("limit", 5))
        phrase, time_range = _WINDOW.get(window, _WINDOW["medium"])

        tracks = client.top_tracks(time_range=time_range, limit=limit)
        spec = ranking_from_tracks(
            title=f"most played · {phrase}",
            tracks=tracks,
            caption="by your listening",
        )
        speech = tracks_speech(f"Your most-played {phrase}", tracks)
        return Presentation(spec=spec, speech=speech)
