"""The race-bar widget: head-to-head bars.

Renders each entry as a labeled block bar sized to its share of the total,
with the value on the right. While data is loading it draws a dim skeleton in
the same footprint, so the panel appears instantly and fills in when the fetch
lands.
"""

from __future__ import annotations

from ..numfmt import human
from ..segment import Row, bar, blank, seg
from ..spec import Entry, RaceBar
from ..text import cell_width, pad, truncate
from ..theme import Theme, series_color

_LABEL_MAX = 32   # cap a single label so a long title can't blow out the row


def _format_value(entry: Entry, spec: RaceBar) -> str:
    """The right-hand readout for one entry."""

    if entry.value is None:
        return "· · ·"
    if spec.as_percent and spec.total > 0:
        return f"{entry.value / spec.total * 100:>5.1f}{spec.unit}"
    unit = spec.unit.strip()
    sep = "" if unit == "%" else " "
    return f"{human(entry.value)}{sep}{unit}".rstrip()


def _entry_row(
    index: int, entry: Entry, label: str, spec: RaceBar, label_w: int, theme: Theme
) -> Row:
    """One line: label, bar, value."""

    color = series_color(theme, index)
    if entry.value is None or spec.total <= 0:
        fraction = 0.0
    else:
        fraction = entry.value / spec.total

    value_color = theme.palette.muted if entry.value is None else color
    return (
        seg(pad(label, label_w), theme.palette.text),
        seg("  "),
        *bar(fraction, theme.bar_width, color, theme),
        seg("  "),
        seg(_format_value(entry, spec), value_color, bold=entry.value is not None),
    )


def build(spec: object, theme: Theme) -> list[Row]:
    """Turn a RaceBar spec into styled rows."""

    if not isinstance(spec, RaceBar):
        raise TypeError(f"race_bar.build expected RaceBar, got {type(spec).__name__}")

    labels = [truncate(e.label, _LABEL_MAX) for e in spec.entries]
    label_w = max(cell_width(lbl) for lbl in labels)
    rows: list[Row] = [
        _entry_row(i, e, labels[i], spec, label_w, theme)
        for i, e in enumerate(spec.entries)
    ]

    if spec.note:
        rows.append(blank())
        marker = theme.glyphs.sparkle if not spec.is_loading else "⋯"
        rows.append((seg(f"{marker} {spec.note}", theme.palette.muted, dim=True),))

    return rows
