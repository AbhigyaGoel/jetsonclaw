"""Invariants for the shape vocabulary: every shape renders to both surfaces
and speaks, and validation fails at the boundary.

    pytest remy_ui/tests/test_shapes.py
    python  remy_ui/tests/test_shapes.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from remy_ui import (  # noqa: E402
    Entry,
    Gauge,
    RaceBar,
    Ranking,
    Series,
    SpecError,
    Status,
    Value,
    to_html,
    to_speech,
    to_terminal,
)

ONE_OF_EACH = [
    Value(title="Stars", value=1240, delta=38),
    RaceBar(title="Poll", entries=(Entry("A", 3), Entry("B", 1))),
    Series(title="Steps", points=(1, 5, 3, 9)),
    Ranking(title="tracks", items=(Entry("x", 5), Entry("y", 2))),
    Status(title="CI", state="passing", level="ok"),
    Gauge(title="DL", value=3, target=6),
]


def test_every_shape_renders_and_speaks() -> None:
    for spec in ONE_OF_EACH:
        assert "\x1b[" in to_terminal(spec), f"{spec.kind}: no ANSI"
        assert "<pre" in to_html(spec), f"{spec.kind}: no HTML"
        said = to_speech(spec)
        assert said and said.endswith("."), f"{spec.kind}: bad speech {said!r}"


def test_ranking_sorts_and_truncates() -> None:
    r = Ranking(title="t", top=2, items=(Entry("low", 1), Entry("high", 9), Entry("mid", 5)))
    ordered = r.ordered
    assert [e.label for e in ordered] == ["high", "mid"]


def test_series_sparkline_length_matches_points() -> None:
    from remy_ui.widgets.series import _sparkline

    pts = (1.0, 4.0, 2.0, 8.0, 3.0)
    line = _sparkline(pts, __import__("remy_ui").CLAWD)
    assert len(line) == len(pts)


def test_value_delta_direction_in_speech() -> None:
    assert "up 38" in to_speech(Value(title="Stars", value=100, delta=38))
    assert "down 5" in to_speech(Value(title="Errs", value=10, delta=-5))


def test_gauge_fraction_clamps() -> None:
    assert Gauge(title="g", value=200, target=100).fraction == 1.0
    assert Gauge(title="g", value=0, target=100).fraction == 0.0


def test_status_rejects_bad_level() -> None:
    try:
        Status(title="t", state="x", level="explode")
    except SpecError:
        return
    raise AssertionError("expected SpecError for an unknown level")


def test_series_rejects_too_few_points() -> None:
    try:
        Series(title="t", points=(1,))
    except SpecError:
        return
    raise AssertionError("expected SpecError for a one-point series")


def test_loading_states_speak_gracefully() -> None:
    assert "yet" in to_speech(Value(title="Temp"))
    assert "yet" in to_speech(Gauge(title="DL", target=5))


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
