"""Synthesizer: your favorite songs by a given artist. The Judge verb.

"my favorite Kanye songs" → pull your top tracks (all-time affinity), filter
to that artist, rank by your real listening. Real-data-only: it never guesses
what you "should" like, it reports which of *your* plays are that artist,
in your order. The judgment is entirely which-of-my-data-matches.
"""

from __future__ import annotations

from typing import Any

from remy_ui import Status

from ..capability import Presentation
from ..context import RemyContext
from ..music import ranking_from_tracks, tracks_speech

# Aliases so "Kanye", "Ye", and "Kanye West" all resolve to the same artist.
_ALIASES = {
    "kanye": "kanye west",
    "ye": "kanye west",
    "kanye west": "kanye west",
}


def _matches(track_artist: str, wanted: str) -> bool:
    return wanted in track_artist.strip().lower()


class TopByArtist:
    name = "spotify.favorite_by_artist"

    def derive(self, params: dict, ctx: RemyContext, client: Any) -> Presentation:
        raw = str(params.get("artist", "")).strip().lower()
        if not raw:
            raise ValueError("top_by_artist requires an 'artist' param")
        wanted = _ALIASES.get(raw, raw)
        display = params.get("artist_display") or raw.title()
        limit = int(params.get("limit", 5))

        # Pull a deep slice of real affinity data, then filter to the artist.
        catalog = client.top_tracks(time_range="long", limit=50)
        mine = [t for t in catalog if _matches(t.artist, wanted)][:limit]

        if not mine:
            spec = Status(
                title=f"favorite {display}",
                state="nothing found",
                level="info",
                detail=f"No {display} in your top tracks.",
            )
            return Presentation(spec=spec, speech=f"I don't see any {display} in your listening.")

        spec = ranking_from_tracks(
            title=f"favorite {display}",
            tracks=mine,
            caption="ranked by your plays",
        )
        speech = tracks_speech(f"Your most-played {display}", mine)
        return Presentation(spec=spec, speech=speech)
