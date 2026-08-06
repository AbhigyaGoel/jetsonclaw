"""Provider registry, the Tell verb. One entry per read-only data source."""

from __future__ import annotations

from .spotify_top import SpotifyTopTracks

PROVIDERS = {
    SpotifyTopTracks.name: SpotifyTopTracks(),
}
