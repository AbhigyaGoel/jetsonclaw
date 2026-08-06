"""The reference Action: add an event to the calendar by voice.

"add dinner with friends friday at 8pm"
    parse    turns it into CalendarEvent(summary, start, end, tz, calendar)
    preview  'Add "Dinner with friends" Friday Aug 7, 8 to 9 PM ... Sound good?'
    execute  client.create_event(...), only after "yes"

This one Action sets the pattern every other Action reuses: the effect is
quarantined behind parse/preview/execute, so the confirmation gate is structural.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from ..capability import ActionError, Result
from ..context import RemyContext
from ..parse.datetime_parse import ParsedTime, TimeParseError, parse_datetime

# Leading command verbs and trailing "...to my calendar" we strip for the title.
_LEAD = re.compile(
    r"^\s*(?:hey\s+remy[,\s]*)?(?:can you\s+|please\s+)?"
    r"(?:remind me to|add|schedule|create|set up|set|put|book|make)\s+(?:an?\s+)?",
    re.IGNORECASE,
)
_TRAIL_CAL = re.compile(
    r"\s+(?:on|to|in)\s+(?:my\s+)?(?:(\w+)\s+)?calendar\s*$", re.IGNORECASE
)
_EDGE_FILLER = re.compile(r"^(?:on|at|for|from|to|with|about)\s+|\s+(?:on|at|for|from)\s*$", re.IGNORECASE)


@dataclass(frozen=True)
class CalendarEvent:
    summary: str
    start: str          # ISO 8601, no offset, timezone carries it
    end: str
    timezone: str
    calendar_id: str
    all_day: bool


def _iso(dt) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%S")


def _title_from(utterance: str, pt: ParsedTime) -> tuple[str, str | None]:
    """Recover the event title and any named calendar from the utterance."""

    text = utterance.strip()
    calendar_name = None
    if m := _TRAIL_CAL.search(text):
        calendar_name = m.group(1)
        text = text[: m.start()]
    text = _LEAD.sub("", text)
    for span in pt.matched:                      # remove the time phrases
        text = re.sub(re.escape(span), " ", text, flags=re.IGNORECASE)
    text = re.sub(r"\s{2,}", " ", text).strip(" ,")
    prev = None
    while prev != text:                          # peel dangling prepositions
        prev = text
        text = _EDGE_FILLER.sub("", text).strip(" ,")
    title = text.strip() or "Event"
    return title[0].upper() + title[1:], calendar_name


def _speak_when(pt: ParsedTime) -> str:
    """A spoken-friendly description of the event's time."""

    if pt.all_day:
        return pt.start.strftime("%A %b ") + str(pt.start.day) + ", all day"
    day = pt.start.strftime("%A %b ") + str(pt.start.day)

    def clock(dt) -> str:
        h = dt.strftime("%I:%M %p").lstrip("0")
        return h.replace(":00", "")             # "8:00 PM" → "8 PM"

    return f"{day}, {clock(pt.start)} to {clock(pt.end)}"


def _when_of(params: "CalendarEvent") -> str:
    """The spoken time of an already-parsed event (from its ISO fields)."""

    return _speak_when(
        ParsedTime(
            start=datetime.fromisoformat(params.start),
            end=datetime.fromisoformat(params.end),
            all_day=params.all_day,
            matched=(),
        )
    )


class CalendarAdd:
    name = "calendar.add"

    def parse(self, utterance: str, ctx: RemyContext) -> CalendarEvent:
        try:
            pt = parse_datetime(utterance, ctx.now)
        except TimeParseError as exc:
            raise ActionError(
                "I couldn't tell when. Try something like 'friday at 8pm'."
            ) from exc
        title, calendar_name = _title_from(utterance, pt)
        return CalendarEvent(
            summary=title,
            start=_iso(pt.start),
            end=_iso(pt.end),
            timezone=ctx.timezone,
            calendar_id=ctx.resolve_calendar(calendar_name),
            all_day=pt.all_day,
        )

    def preview(self, params: CalendarEvent, ctx: RemyContext) -> str:
        where = "your calendar"
        for name, cid in ctx.calendars.items():
            if cid == params.calendar_id:
                where = f"your {name} calendar"
                break
        return f'Add "{params.summary}" {_when_of(params)} to {where}. Sound good?'

    def execute(self, params: CalendarEvent, client: Any) -> Result:
        resp = client.create_event(
            summary=params.summary,
            start=params.start,
            end=params.end,
            timezone=params.timezone,
            calendar_id=params.calendar_id,
            all_day=params.all_day,
        )
        return Result(
            ok=True,
            speech=f"Done. {params.summary} is on for {_when_of(params)}.",
            detail=resp.get("htmlLink", ""),
            data=resp,
        )
