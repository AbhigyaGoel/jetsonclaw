"""The target-agnostic intermediate representation.

Widgets don't emit ANSI or HTML. They emit *rows of styled segments*. A
renderer later turns those segments into whatever the surface speaks,
ANSI escape codes for the TUI, span tags for the web PWA. This is the
seam that lets one widget render identically in both places.

Everything here is immutable: a Segment is frozen, a Row is a tuple.
"""

from __future__ import annotations

from typing import NamedTuple, Optional, Sequence

from .theme import Color


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
    """The printed width of a row, ignoring styling.

    Assumes one cell per character. The box-drawing, block, and sparkle
    glyphs we use are all single-width, so this holds for our widgets.
    """

    return sum(len(s.text) for s in r)


def content_width(rows: Sequence[Row]) -> int:
    """Widest visible row in a block, used to size boxes."""

    return max((visible_width(r) for r in rows), default=0)
