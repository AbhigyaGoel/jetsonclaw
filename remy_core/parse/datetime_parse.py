"""Natural-language date/time → concrete start/end.

Scoped to how a person actually talks to an assistant: "tomorrow at 8pm",
"friday", "next monday 3-4", "aug 12 for 2 hours". Not a general grammar,
a tight, deterministic parser whose guesses the confirmation line will catch.

Every result also carries the matched substrings, so the caller can strip
them out to recover the event title. `now` is injected: no hidden clock, so
"friday" resolves the same in a test as in production.

Swap-in note: dateparser.search.search_dates() could replace this if broader
coverage is ever needed; kept dependency-free for the Jetson and for control
over the evening-bias and span extraction below.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta

_WEEKDAYS = {
    "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
    "friday": 4, "saturday": 5, "sunday": 6,
    "mon": 0, "tue": 1, "tues": 1, "wed": 2, "thu": 3, "thur": 3,
    "thurs": 3, "fri": 4, "sat": 5, "sun": 6,
}
_MONTHS = {
    "jan": 1, "january": 1, "feb": 2, "february": 2, "mar": 3, "march": 3,
    "apr": 4, "april": 4, "may": 5, "jun": 6, "june": 6, "jul": 7, "july": 7,
    "aug": 8, "august": 8, "sep": 9, "sept": 9, "september": 9, "oct": 10,
    "october": 10, "nov": 11, "november": 11, "dec": 12, "december": 12,
}


@dataclass(frozen=True)
class ParsedTime:
    start: datetime
    end: datetime
    all_day: bool
    matched: tuple[str, ...]   # substrings consumed, for title recovery


class TimeParseError(ValueError):
    """No usable date/time found in the utterance."""


def _to_24h(hour: int, minute: int, meridiem: str | None) -> time:
    """Resolve an hour to 24h. No meridiem → evening bias (1 to 9 ⇒ pm).

    Covers the way plans actually get spoken ("at 8", "at 9" = evening). 10
    and 11 stay literal (morning classes); anything the bias gets wrong is
    surfaced by the spoken confirmation before the event is ever created.
    """

    if meridiem == "pm" and hour != 12:
        hour += 12
    elif meridiem == "am" and hour == 12:
        hour = 0
    elif meridiem is None and 1 <= hour <= 9:
        hour += 12
    return time(hour % 24, minute)


def _find_day(text: str, now: datetime) -> tuple[date | None, list[str]]:
    """The date anchor, if any, plus the substrings it consumed."""

    if m := re.search(r"\btoday\b|\btonight\b", text):
        return now.date(), [m.group(0)]
    if m := re.search(r"\btomorrow\b", text):
        return (now + timedelta(days=1)).date(), [m.group(0)]

    # "next friday" / "this friday" / "friday"
    if m := re.search(r"\b(next|this)?\s*(" + "|".join(_WEEKDAYS) + r")\b", text):
        nxt = m.group(1) == "next"
        wd = _WEEKDAYS[m.group(2)]
        base = (wd - now.weekday()) % 7
        if nxt:
            base = base + 7 if base else 7      # the following week's weekday
        return now.date() + timedelta(days=base), [m.group(0).strip()]

    # "aug 12", "august 12th"
    months = "|".join(_MONTHS)
    if m := re.search(rf"\b({months})\.?\s+(\d{{1,2}})(?:st|nd|rd|th)?\b", text):
        month, day = _MONTHS[m.group(1)], int(m.group(2))
        year = now.year + (1 if (month, day) < (now.month, now.day) else 0)
        return date(year, month, day), [m.group(0)]

    # "8/12" (month/day)
    if m := re.search(r"\b(\d{1,2})/(\d{1,2})\b", text):
        month, day = int(m.group(1)), int(m.group(2))
        if 1 <= month <= 12 and 1 <= day <= 31:
            year = now.year + (1 if (month, day) < (now.month, now.day) else 0)
            return date(year, month, day), [m.group(0)]

    return None, []


def _find_times(text: str) -> tuple[list[time], list[str]]:
    """Zero, one, or two clock times (a range), plus consumed substrings."""

    tt = r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)?"
    # A range: "8-10pm", "8 to 9", "from 3 to 4pm".
    rng = re.search(rf"\b(?:from\s+)?{tt}\s*(?:-|–|to|until)\s*{tt}\b", text)
    if rng:
        h1, m1, mer1, h2, m2, mer2 = rng.groups()
        mer1 = mer1 or mer2          # "8 to 9pm" → both pm
        t1 = _to_24h(int(h1), int(m1 or 0), mer1)
        t2 = _to_24h(int(h2), int(m2 or 0), mer2)
        return [t1, t2], [rng.group(0)]

    if re.search(r"\bnoon\b", text):
        return [time(12, 0)], ["noon"]
    if re.search(r"\bmidnight\b", text):
        return [time(0, 0)], ["midnight"]

    # A single time: "at 8", "8pm", "8:30". Bare hours need "at" to avoid
    # grabbing quantities like "2 hours".
    single = re.search(r"\bat\s+(\d{1,2})(?::(\d{2}))?\s*(am|pm)?\b", text)
    ampm = re.search(r"\b(\d{1,2})(?::(\d{2}))?\s*(am|pm)\b", text)
    chosen = single or ampm
    if chosen:
        h, mnt, mer = chosen.group(1), chosen.group(2), chosen.group(3)
        return [_to_24h(int(h), int(mnt or 0), mer)], [chosen.group(0)]

    if re.search(r"\btonight\b", text):
        return [time(19, 0)], []      # evening default; day already matched

    return [], []


def _find_duration(text: str) -> tuple[timedelta | None, list[str]]:
    if m := re.search(r"\bfor\s+(\d+)\s*(hours?|hrs?|h|minutes?|mins?|m)\b", text):
        n, unit = int(m.group(1)), m.group(2)
        delta = timedelta(hours=n) if unit.startswith(("h", "hr")) else timedelta(minutes=n)
        return delta, [m.group(0)]
    return None, []


def parse_datetime(text: str, now: datetime) -> ParsedTime:
    """Parse a lowercased utterance into a start/end window."""

    text = text.lower()
    matched: list[str] = []

    day, day_spans = _find_day(text, now)
    times, time_spans = _find_times(text)
    dur, dur_spans = _find_duration(text)
    matched += day_spans + time_spans + dur_spans

    if not times and day is None:
        raise TimeParseError("no date or time found")

    if times:
        base = day or now.date()
        start = datetime.combine(base, times[0])
        # No explicit day and the time already passed today → assume tomorrow.
        if day is None and start < now:
            start += timedelta(days=1)
        if len(times) >= 2:
            end = datetime.combine(start.date(), times[1])
            if end <= start:
                end += timedelta(hours=1)
        else:
            end = start + (dur or timedelta(hours=1))
        return ParsedTime(start, end, all_day=False, matched=tuple(matched))

    # Day only → an all-day event.
    start = datetime.combine(day, time(0, 0))
    return ParsedTime(start, start + timedelta(days=1), all_day=True, matched=tuple(matched))
