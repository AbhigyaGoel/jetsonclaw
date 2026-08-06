"""The race-bar widget: head-to-head percentage bars.

This is the widget behind "Abdul vs Stevens, live." It renders each entry
as a labeled block bar sized to its share of the total, with the value on
the right. While data is loading it draws a dim skeleton in the same
footprint so the panel appears instantly and fills in when the fetch lands.
"""

from __future__ import annotations

from typing import Sequence

from ..numfmt import human
from ..segment import Row, blank, seg
from ..spec import Entry, RaceBar
from ..theme import Theme, series_color


def _label_width(entries: Sequence[Entry]) -> int:
    """Align all bars by padding labels to the longest one."""

    return max(len(e.label) for e in entries)


def _bar(fraction: float, width: int, color, theme: Theme) -> tuple:
    """A block bar: filled cells in `color`, remainder as a dim track."""

    filled = round(max(0.0, min(1.0, fraction)) * width)
    g = theme.glyphs
    return (
        seg(g.bar_full * filled, color),
        seg(g.bar_empty * (width - filled), None, dim=True),
    )


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
    index: int, entry: Entry, spec: RaceBar, label_w: int, theme: Theme
) -> Row:
    """One line: label, bar, value."""

    color = series_color(theme, index)
    if entry.value is None or spec.total <= 0:
        fraction = 0.0
    else:
        fraction = entry.value / spec.total

    label = seg(entry.label.ljust(label_w), theme.palette.text)
    value_text = _format_value(entry, spec)
    value_color = theme.palette.muted if entry.value is None else color

    return (
        label,
        seg("  "),
        *_bar(fraction, theme.bar_width, color, theme),
        seg("  "),
        seg(value_text, value_color, bold=entry.value is not None),
    )


def build(spec: object, theme: Theme) -> list[Row]:
    """Turn a RaceBar spec into styled rows."""

    if not isinstance(spec, RaceBar):
        raise TypeError(f"race_bar.build expected RaceBar, got {type(spec).__name__}")

    label_w = _label_width(spec.entries)
    rows: list[Row] = [
        _entry_row(i, e, spec, label_w, theme) for i, e in enumerate(spec.entries)
    ]

    if spec.note:
        rows.append(blank())
        color = theme.palette.muted
        marker = theme.glyphs.sparkle if not spec.is_loading else "⋯"
        rows.append((seg(f"{marker} {spec.note}", color, dim=True),))

    return rows
