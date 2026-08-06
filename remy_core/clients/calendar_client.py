"""The calendar backend seam.

An Action never talks to Google directly, it talks to this small interface.
That's what makes calendar-add testable here (FakeCalendarClient records the
call) and identical on the Jetson (a real adapter wraps REMY's Google creds).

Real adapter mapping, a create_event(...) call maps 1:1 onto the Google
Calendar `create_event` tool REMY already has access to:

    summary      → summary
    start (ISO)  → startTime
    end   (ISO)  → endTime
    timezone     → timeZone
    calendar_id  → calendarId
    all_day      → allDay

Implement `create_event` there by calling that tool; everything above it,
parsing, previewing, confirming, stays unchanged.
"""

from __future__ import annotations

from typing import Protocol


class CalendarClient(Protocol):
    """Anything that can create a calendar event."""

    def create_event(
        self,
        *,
        summary: str,
        start: str,
        end: str,
        timezone: str,
        calendar_id: str,
        all_day: bool,
    ) -> dict:
        """Create the event and return the backend's response (id, link)."""


class FakeCalendarClient:
    """A test double. Records every create call; invents an id and link."""

    def __init__(self) -> None:
        self.created: list[dict] = []

    def create_event(self, **kwargs) -> dict:
        self.created.append(kwargs)
        n = len(self.created)
        return {
            "id": f"evt_fake_{n}",
            "htmlLink": f"https://calendar.google.com/event?eid=fake{n}",
        }
