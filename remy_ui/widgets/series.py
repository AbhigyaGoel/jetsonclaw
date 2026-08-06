"""The `series` shape: a value over time, drawn as a sparkline.

Trends, forecasts, history, anything you'd want to see the *shape* of
rather than a single number. One line of block glyphs plus a stat readout.
"""

from __future__ import annotations

from ..numfmt import human
from ..segment import Row, seg
from ..spec import Series
from ..theme import Theme


def _sparkline(points: tuple[float, ...], theme: Theme) -> str:
    ramp = theme.glyphs.spark
    lo, hi = min(points), max(points)
    span = hi - lo
    if span == 0:
        # Flat line, sit in the middle of the ramp.
        return ramp[len(ramp) // 2] * len(points)
    out = []
    for p in points:
        idx = round((p - lo) / span * (len(ramp) - 1))
        out.append(ramp[idx])
    return "".join(out)


def build(spec: object, theme: Theme) -> list[Row]:
    if not isinstance(spec, Series):
        raise TypeError(f"series.build expected Series, got {type(spec).__name__}")

    p = theme.palette
    line = _sparkline(spec.points, theme)
    rows: list[Row] = [(seg(line, p.accent, bold=True),)]

    last, lo, hi = spec.points[-1], min(spec.points), max(spec.points)
    unit = f"{spec.unit}" if spec.unit else ""
    stat = f"last {human(last)}{unit}   low {human(lo)}   high {human(hi)}"
    rows.append((seg(stat, p.muted),))

    if spec.caption:
        rows.append((seg(spec.caption, p.muted, dim=True),))
    return rows
