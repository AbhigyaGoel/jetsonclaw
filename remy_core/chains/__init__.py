"""Chain registry, the Chain verb. Capabilities that sequence other
capabilities (read steps to gather, a gated write step to commit)."""

from __future__ import annotations

from .playlist_from_artist import PlaylistFromArtist

CHAINS = {
    PlaylistFromArtist.name: PlaylistFromArtist(),
}
