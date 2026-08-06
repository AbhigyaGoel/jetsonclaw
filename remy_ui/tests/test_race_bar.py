"""Core invariants for the race-bar path. Runs under pytest or standalone:

    pytest remy_ui/tests/test_race_bar.py
    python  remy_ui/tests/test_race_bar.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# Allow running as a plain script (no installed package on the path).
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from remy_ui import CLAWD, Entry, RaceBar, SpecError, to_html, to_terminal  # noqa: E402
from remy_ui.segment import content_width  # noqa: E402
from remy_ui.widgets import race_bar  # noqa: E402


def test_rejects_single_entry() -> None:
    try:
        RaceBar(title="x", entries=(Entry("solo", 1),))
    except SpecError:
        return
    raise AssertionError("expected SpecError for a one-entry race")


def test_rejects_blank_title() -> None:
    try:
        RaceBar(title="  ", entries=(Entry("a", 1), Entry("b", 1)))
    except SpecError:
        return
    raise AssertionError("expected SpecError for a blank title")


def test_rejects_negative_value() -> None:
    try:
        Entry("a", -5)
    except SpecError:
        return
    raise AssertionError("expected SpecError for a negative value")


def test_percentages_reflect_shares() -> None:
    spec = RaceBar(title="t", entries=(Entry("a", 75), Entry("b", 25)))
    text = to_terminal(spec)
    assert "75.0%" in text
    assert "25.0%" in text


def test_skeleton_shows_placeholder_not_percent() -> None:
    spec = RaceBar(title="t", entries=(Entry("a"), Entry("b")))
    assert spec.is_loading
    text = to_terminal(spec)
    assert "· · ·" in text
    assert "%" not in text          # no phantom percentages while loading


def test_absolute_unit_formats_clean() -> None:
    spec = RaceBar(
        title="t", unit=" votes", as_percent=False,
        entries=(Entry("a", 1200), Entry("b", 900)),
    )
    text = to_terminal(spec)
    assert "1,200 votes" in text     # thousands separator, single space
    assert "  votes" not in text     # regression: double-space bug


def test_rows_are_rectangular() -> None:
    """Every content row must share one width so borders align."""
    spec = RaceBar(title="t", entries=(Entry("Abdul", 54), Entry("Stevens", 46)))
    rows = race_bar.build(spec, CLAWD)
    widths = {content_width([r]) for r in rows if r}
    # Entry rows share a width; the note row may differ, check entry rows only.
    entry_widths = {content_width([rows[0]]), content_width([rows[1]])}
    assert len(entry_widths) == 1, f"entry rows misaligned: {widths}"


def test_both_surfaces_render() -> None:
    spec = RaceBar(title="t", entries=(Entry("a", 1), Entry("b", 1)))
    assert "\x1b[" in to_terminal(spec)      # ANSI present
    assert "<pre" in to_html(spec)           # HTML present


def test_html_escapes_untrusted_labels() -> None:
    spec = RaceBar(title="t", entries=(Entry("<script>", 1), Entry("b", 1)))
    html = to_html(spec)
    assert "<script>" not in html
    assert "&lt;script&gt;" in html


def _run_all() -> int:
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failed = 0
    for t in tests:
        try:
            t()
            print(f"  ok  {t.__name__}")
        except Exception as exc:  # noqa: BLE001 - test harness surface
            failed += 1
            print(f"FAIL  {t.__name__}: {exc}")
    print(f"\n{len(tests) - failed}/{len(tests)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(_run_all())
