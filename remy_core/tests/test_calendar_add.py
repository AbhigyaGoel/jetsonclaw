"""The full calendar-add flow: parse → preview → (gate) → execute.

    python remy_core/tests/test_calendar_add.py
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from remy_core import ActionError, RemyContext, plan  # noqa: E402
from remy_core.actions import ACTIONS  # noqa: E402
from remy_core.clients import FakeCalendarClient  # noqa: E402

NOW = datetime(2026, 8, 5, 14, 0)
ACTION = ACTIONS["calendar.add"]


def _ctx(**kw) -> RemyContext:
    return RemyContext(now=NOW, calendars={"school": "abhigyag@usc.edu"}, **kw)


def test_title_is_cleaned() -> None:
    ev = ACTION.parse("add dinner with friends friday at 8pm", _ctx())
    assert ev.summary == "Dinner with friends"


def test_time_becomes_iso_with_tz() -> None:
    ev = ACTION.parse("add dinner friday at 8pm", _ctx())
    assert ev.start == "2026-08-07T20:00:00"
    assert ev.end == "2026-08-07T21:00:00"
    assert ev.timezone == "America/Los_Angeles"


def test_named_calendar_resolves() -> None:
    ev = ACTION.parse("add office hours tuesday at 3pm to my school calendar", _ctx())
    assert ev.calendar_id == "abhigyag@usc.edu"
    assert "calendar" not in ev.summary.lower()


def test_preview_reads_naturally() -> None:
    pending = plan(ACTION, "add dinner with friends friday at 8pm", _ctx())
    assert "Dinner with friends" in pending.confirm
    assert "Friday" in pending.confirm
    assert pending.confirm.rstrip().endswith("good?")


def test_nothing_happens_before_run() -> None:
    client = FakeCalendarClient()
    plan(ACTION, "add gym tomorrow at 7am", _ctx())   # planned, not run
    assert client.created == []                        # gate held


def test_execute_creates_event() -> None:
    client = FakeCalendarClient()
    pending = plan(ACTION, "add gym tomorrow at 7am", _ctx())
    result = pending.run(client)
    assert result.ok
    assert len(client.created) == 1
    assert client.created[0]["summary"] == "Gym"
    assert "gym is on" in result.speech.lower()


def test_unparseable_raises_actionerror() -> None:
    try:
        ACTION.parse("add a thing", _ctx())
    except ActionError as exc:
        assert "when" in str(exc).lower()   # spoken-friendly hint
        return
    raise AssertionError("expected ActionError")


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
