"""Ambient context every capability runs against.

The single source of "now", the user's timezone, and which calendars exist.
Injected, never global, so tests pin a fixed `now` and REMY passes the real
one. This is what lets "friday at 8" resolve deterministically.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class RemyContext:
    """What a capability needs to know about the world right now."""

    now: datetime                      # the reference instant (naive local time)
    timezone: str = "America/Los_Angeles"   # IANA tz, USC / LA by default
    default_calendar: str = "primary"        # calendar_id used when unspecified
    # Friendly name → calendar_id, e.g. {"school": "abhigyag@usc.edu"}.
    calendars: dict = field(default_factory=dict)

    def resolve_calendar(self, name: str | None) -> str:
        """Map a spoken calendar name to an id, falling back to the default."""

        if not name:
            return self.default_calendar
        return self.calendars.get(name.strip().lower(), self.default_calendar)
