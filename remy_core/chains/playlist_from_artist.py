"""Chain: a playlist of your favorite songs by an artist, the 4th verb.

    "make a playlist of my favorite Kanye and play it"
        read  (Judge): favorite_by_artist → your top Ye, real data
        write (Act):   create_playlist(+ play), gated by a yes

The read step runs during `gather()` so REMY can *show* the tracks and name
the count in its confirmation. Nothing is written until PendingChain.run().
"""

from __future__ import annotations

from typing import Any

from ..actions import ACTIONS
from ..actions.create_playlist import PlaylistSpec
from ..capability import PendingChain, Presentation, Result
from ..context import RemyContext
from ..synthesizers import SYNTHESIZERS


class PlaylistFromArtist:
    name = "chain.playlist_from_artist"

    def gather(self, params: dict, ctx: RemyContext, clients: dict) -> PendingChain:
        spotify = clients["spotify"]
        display = params.get("artist_display") or str(params.get("artist", "")).title()
        play = bool(params.get("play", False))

        # Read step (no side effects): which of my plays are this artist.
        synth = SYNTHESIZERS["spotify.favorite_by_artist"]
        picked = synth.derive(
            {"artist": params["artist"], "artist_display": display,
             "limit": int(params.get("limit", 10))},
            ctx, spotify,
        )

        # Nothing to act on → no gate, just report the read step's miss.
        if getattr(picked.spec, "kind", None) != "ranking":
            return PendingChain(
                confirm="",
                _commit=lambda _cl, p=picked: Result(ok=False, speech=p.speech),
                show=picked,
            )

        tracks = tuple(e.label for e in picked.spec.items)
        spec = PlaylistSpec(
            name=f"REMY's {display} picks", track_names=tracks, play=play
        )
        action = ACTIONS["spotify.create_playlist"]

        def commit(cl: dict, _spec: PlaylistSpec = spec) -> Result:
            return action.execute(_spec, cl["spotify"])

        return PendingChain(
            confirm=action.preview(spec, ctx),
            _commit=commit,
            show=picked,          # show the tracks while asking
        )
