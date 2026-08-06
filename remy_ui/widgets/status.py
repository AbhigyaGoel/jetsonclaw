"""The `status` shape: a discrete state with a semantic level.

Build green/red, server up/down, package delivered, "all clear." A colored
dot carries the meaning; the state text sits beside it.
"""

from __future__ import annotations

from ..segment import Row, seg
from ..spec import Status
from ..theme import Theme, level_color


def build(spec: object, theme: Theme) -> list[Row]:
    if not isinstance(spec, Status):
        raise TypeError(f"status.build expected Status, got {type(spec).__name__}")

    p = theme.palette
    color = level_color(theme, spec.level)

    badge: Row = (
        seg(f"{theme.glyphs.dot} ", color),
        seg(spec.state, color, bold=True),
    )
    rows: list[Row] = [badge]
    if spec.detail:
        rows.append((seg(spec.detail, p.muted, dim=True),))
    return rows
