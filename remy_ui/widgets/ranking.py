"""The `ranking` shape: an ordered leaderboard with mini-bars.

Top tracks, top processes, standings, a todo list by priority. Items sort
high->low automatically; a short bar gives relative magnitude at a glance.
"""

from __future__ import annotations

from ..numfmt import human
from ..segment import Row, bar, seg
from ..spec import Entry, Ranking
from ..text import cell_width, pad, truncate
from ..theme import Theme, series_color

_BAR_WIDTH = 14
_LABEL_MAX = 32


def _row(rank: int, entry: Entry, label: str, top_value: float, label_w: int, theme: Theme) -> Row:
    p = theme.palette
    color = series_color(theme, rank - 1)
    value = entry.value if entry.value is not None else 0
    frac = 0.0 if top_value <= 0 else value / top_value
    return (
        seg(f"{rank}. ", p.muted),
        seg(pad(label, label_w), p.text),
        seg("  "),
        *bar(frac, _BAR_WIDTH, color, theme),
        seg("  "),
        seg(human(value), color, bold=True),
    )


def build(spec: object, theme: Theme) -> list[Row]:
    if not isinstance(spec, Ranking):
        raise TypeError(f"ranking.build expected Ranking, got {type(spec).__name__}")

    items = spec.ordered
    top_value = max((e.value if e.value is not None else 0) for e in items)
    labels = [truncate(e.label, _LABEL_MAX) for e in items]
    label_w = max(cell_width(lbl) for lbl in labels)

    rows: list[Row] = [
        _row(i + 1, e, labels[i], top_value, label_w, theme)
        for i, e in enumerate(items)
    ]
    if spec.caption:
        rows.append((seg(spec.caption, theme.palette.muted, dim=True),))
    return rows
