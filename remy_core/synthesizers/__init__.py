"""Synthesizer registry, the Judge verb. Grounded, real-data-only answers."""

from __future__ import annotations

from .top_by_artist import TopByArtist

SYNTHESIZERS = {
    TopByArtist.name: TopByArtist(),
}
