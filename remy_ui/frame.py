"""Draw a rounded, titled panel around a block of rows.

The box is not special, it's just more styled rows. By building the border
as `Segment`s too, the frame stays target-agnostic: terminal and HTML
renderers encode it with the exact same code path as widget content.

    ╭─ ✻ dorm pizza poll ──────────────────╮
    │  Pepperoni  ███████████████░░░░░  54% │
    │  Mushroom   ████████████░░░░░░░░  46% │
    ╰───────────────────────────────────────╯
"""

from __future__ import annotations

from typing import Sequence

from .segment import Row, Segment, content_width, seg, visible_width
from .theme import Theme


def _pad_row(content: Row, field_width: int, pad: int, vertical: str) -> Row:
    """Wrap one content row in vertical borders with inner padding."""

    used = visible_width(content)
    right_gap = field_width - used
    return (
        seg(vertical, None, dim=True),
        seg(" " * pad),
        *content,
        seg(" " * (right_gap + pad)),
        seg(vertical, None, dim=True),
    )


def frame(
    title: str, rows: Sequence[Row], theme: Theme, min_width: int = 0
) -> list[Row]:
    """Return `rows` wrapped in a titled rounded panel.

    `min_width` forces a minimum inner span, so a group of related panels
    (e.g. the lifecycle of one race) can be rendered at a uniform width
    instead of each sizing itself independently and looking ragged.
    """

    g = theme.glyphs
    accent = theme.palette.accent
    pad = theme.pad

    # Visible width of the decorated title: dash + space + ✻ + space + title + space.
    prefix_visible = len(title) + 5
    inner_span = max(content_width(rows) + 2 * pad, prefix_visible + 1, min_width)
    field_width = inner_span - 2 * pad
    dashes_after = inner_span - prefix_visible

    top: Row = (
        seg(g.top_left, None, dim=True),
        seg(g.horizontal + " ", None, dim=True),
        seg(g.sparkle, accent),
        seg(" "),
        seg(title, accent, bold=True),
        seg(" "),
        seg(g.horizontal * dashes_after, None, dim=True),
        seg(g.top_right, None, dim=True),
    )
    bottom: Row = (
        seg(g.bottom_left, None, dim=True),
        seg(g.horizontal * inner_span, None, dim=True),
        seg(g.bottom_right, None, dim=True),
    )

    body: list[Row] = [_pad_row(r, field_width, pad, g.vertical) for r in rows]
    return [top, *body, bottom]
