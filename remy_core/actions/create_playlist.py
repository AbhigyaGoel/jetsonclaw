"""Action: create a Spotify playlist from a set of tracks, optionally playing it.

Unlike calendar-add, this Action's params come from a *prior chain step*
(the tracks a Synthesizer picked), not from parsing the utterance, so its
`parse` refuses direct use. It exists to be the effectful tail of a Chain,
and it reuses the same preview/execute gate every Action has.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..capability import ActionError, Result


@dataclass(frozen=True)
class PlaylistSpec:
    name: str
    track_names: tuple[str, ...]
    play: bool = False


class CreatePlaylist:
    name = "spotify.create_playlist"

    def parse(self, utterance: str, ctx) -> PlaylistSpec:
        raise ActionError(
            "Creating a playlist needs songs. Ask for it as 'a playlist of my ...'."
        )

    def preview(self, params: PlaylistSpec, ctx) -> str:
        n = len(params.track_names)
        songs = "song" if n == 1 else "songs"
        tail = " and start it" if params.play else ""
        return f'Make a playlist "{params.name}" with {n} {songs}{tail}. Sound good?'

    def execute(self, params: PlaylistSpec, client: Any) -> Result:
        resp = client.create_playlist(params.name, list(params.track_names))
        if params.play:
            client.play(list(params.track_names))
        n = len(params.track_names)
        if params.play:
            speech = f'Done. "{params.name}" is playing, {n} songs.'
        else:
            speech = f'Saved "{params.name}", {n} songs.'
        return Result(ok=True, speech=speech, detail=resp.get("url", ""), data=resp)
