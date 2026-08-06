"""The `ranking` shape: an ordered leaderboard with mini-bars.

Top tracks, top processes, standings, a todo list by priority. Items sort
high→low automatically; a short bar gives relative magnitude at a glance.
"""

from __future__ import annotations

from ..numfmt import human
from ..segment import Row, seg
from ..spec import Entry, Ranking
from ..theme import Theme, series_color

_BAR_WIDTH = 14


def _row(rank: int, entry: Entry, top_value: float, label_w: int, theme: Theme) -> Row:
    p = theme.palette
    color = series_color(theme, rank - 1)
    value = entry.value or 0
    frac = 0.0 if top_value <= 0 else value / top_value
    filled = round(frac * _BAR_WIDTH)

    return (
        seg(f"{rank}. ", p.muted),
        seg(entry.label.ljust(label_w), p.text),
        seg("  "),
        seg(theme.glyphs.bar_full * filled, color),
        seg(theme.glyphs.bar_empty * (_BAR_WIDTH - filled), None, dim=True),
        seg("  "),
        seg(human(value), color, bold=True),
    )


def build(spec: object, theme: Theme) -> list[Row]:
    if not isinstance(spec, Ranking):
        raise TypeError(f"ranking.build expected Ranking, got {type(spec).__name__}")

    items = spec.ordered
    top_value = max((e.value or 0) for e in items)
    label_w = max(len(e.label) for e in items)

    rows: list[Row] = [
        _row(i + 1, e, top_value, label_w, theme) for i, e in enumerate(items)
    ]
    if spec.caption:
        rows.append((seg(spec.caption, theme.palette.muted, dim=True),))
    return rows
