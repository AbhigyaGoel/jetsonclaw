"""The target-agnostic intermediate representation.

Widgets don't emit ANSI or HTML. They emit *rows of styled segments*. A
renderer later turns those segments into whatever the surface speaks,
ANSI escape codes for the TUI, span tags for the web PWA. This is the
seam that lets one widget render identically in both places.

Everything here is immutable: a Segment is frozen, a Row is a tuple.
"""

from __future__ import annotations

import math
from typing import NamedTuple, Optional, Sequence

from .text import cell_width
from .theme import Color, Theme


class Segment(NamedTuple):
    """A run of text with a single style. The atom of rendered output."""

    text: str
    color: Optional[Color] = None
    bold: bool = False
    dim: bool = False


# A Row is an ordered run of segments. A widget returns a sequence of rows.
Row = tuple[Segment, ...]


def seg(
    text: str,
    color: Optional[Color] = None,
    *,
    bold: bool = False,
    dim: bool = False,
) -> Segment:
    """Terse constructor for a styled segment."""

    return Segment(text=text, color=color, bold=bold, dim=dim)


def blank() -> Row:
    """An empty spacer row."""

    return ()


def visible_width(r: Row) -> int:
    """The printed width of a row in terminal cells, ignoring styling."""

    return sum(cell_width(s.text) for s in r)


def content_width(rows: Sequence[Row]) -> int:
    """Widest visible row in a block, used to size boxes."""

    return max((visible_width(r) for r in rows), default=0)


def bar(fraction: float, width: int, color: Optional[Color], theme: Theme) -> Row:
    """A block bar: filled cells in `color`, the remainder a dim track.

    Clamps to [0, 1] and treats a non-finite fraction (NaN/inf from bad data)
    as empty, so a garbage value renders a blank bar instead of crashing.
    """

    frac = fraction if math.isfinite(fraction) else 0.0
    filled = round(max(0.0, min(1.0, frac)) * width)
    g = theme.glyphs
    return (
        seg(g.bar_full * filled, color),
        seg(g.bar_empty * (width - filled), None, dim=True),
    )
