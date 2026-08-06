"""Backend seams, the interfaces capabilities call instead of real services."""

from __future__ import annotations

from .calendar_client import CalendarClient, FakeCalendarClient
from .spotify_client import FakeSpotifyClient, SpotifyClient, Track

__all__ = [
    "CalendarClient",
    "FakeCalendarClient",
    "SpotifyClient",
    "FakeSpotifyClient",
    "Track",
]
