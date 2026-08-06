"""Parser invariants, pinned against a fixed `now` = Wed 2026-08-05 14:00.

    python remy_core/tests/test_datetime_parse.py
"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from remy_core.parse.datetime_parse import (  # noqa: E402
    TimeParseError,
    parse_datetime,
)

NOW = datetime(2026, 8, 5, 14, 0)   # Wednesday afternoon


def test_tomorrow_at_8pm() -> None:
    pt = parse_datetime("dinner tomorrow at 8pm", NOW)
    assert pt.start == datetime(2026, 8, 6, 20, 0)
    assert pt.end == datetime(2026, 8, 6, 21, 0)   # default 1h
    assert not pt.all_day


def test_evening_bias_no_meridiem() -> None:
    # "at 8" with no am/pm → 8pm, not 8am.
    pt = parse_datetime("call mom tomorrow at 8", NOW)
    assert pt.start.hour == 20


def test_weekday_resolves_forward() -> None:
    pt = parse_datetime("gym friday at 9am", NOW)
    assert pt.start.weekday() == 4          # Friday
    assert pt.start.hour == 9
    assert pt.start.date() == datetime(2026, 8, 7).date()


def test_next_weekday_jumps_a_week() -> None:
    this_fri = parse_datetime("friday at 5pm", NOW).start.date()
    next_fri = parse_datetime("next friday at 5pm", NOW).start.date()
    assert (next_fri - this_fri) == timedelta(days=7)


def test_explicit_range() -> None:
    pt = parse_datetime("study block friday 3 to 5pm", NOW)
    assert pt.start.hour == 15 and pt.end.hour == 17


def test_duration_sets_end() -> None:
    pt = parse_datetime("lab tomorrow at 2pm for 3 hours", NOW)
    assert pt.end - pt.start == timedelta(hours=3)


def test_month_day() -> None:
    pt = parse_datetime("flight aug 20 at 6am", NOW)
    assert (pt.start.month, pt.start.day, pt.start.hour) == (8, 20, 6)


def test_day_only_is_all_day() -> None:
    pt = parse_datetime("mom's birthday on aug 30", NOW)
    assert pt.all_day
    assert pt.start.date() == datetime(2026, 8, 30).date()


def test_past_time_today_rolls_tomorrow() -> None:
    # 9am already passed at 2pm today, no explicit day → tomorrow.
    pt = parse_datetime("at 9am", NOW)
    assert pt.start.date() == (NOW + timedelta(days=1)).date()


def test_noon_and_midnight() -> None:
    assert parse_datetime("lunch tomorrow at noon", NOW).start.hour == 12
    assert parse_datetime("tomorrow midnight", NOW).start.hour == 0


def test_no_time_raises() -> None:
    try:
        parse_datetime("just some text with no when", NOW)
    except TimeParseError:
        return
    raise AssertionError("expected TimeParseError")


def _run_all() -> int:
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failed = 0
    for t in tests:
        try:
            t()
            print(f"  ok  {t.__name__}")
        except Exception as exc:  # noqa: BLE001
            failed += 1
            print(f"FAIL  {t.__name__}: {exc}")
    print(f"\n{len(tests) - failed}/{len(tests)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(_run_all())
