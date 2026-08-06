"""Encode styled rows to ANSI 24-bit escape sequences for the TUI."""

from __future__ import annotations

from typing import Sequence

from ..segment import Row, Segment
from ..theme import Theme

_RESET = "\x1b[0m"


def _style(seg: Segment, theme: Theme) -> str:
    """The escape prefix for one segment's style."""

    codes: list[str] = []
    if seg.bold:
        codes.append("1")
    if seg.dim:
        # If no explicit color, use the theme's faint color so "dim" reads
        # consistently across terminals that ignore the SGR dim attribute.
        color = seg.color or theme.palette.faint
        codes.append(f"38;2;{color.r};{color.g};{color.b}")
    elif seg.color is not None:
        codes.append(f"38;2;{seg.color.r};{seg.color.g};{seg.color.b}")
    if not codes:
        return ""
    return "\x1b[" + ";".join(codes) + "m"


def _line(row: Row, theme: Theme) -> str:
    out: list[str] = []
    for s in row:
        prefix = _style(s, theme)
        if prefix:
            out.append(prefix + s.text + _RESET)
        else:
            out.append(s.text)
    return "".join(out)


def encode(rows: Sequence[Row], theme: Theme) -> str:
    """Join rows into a single printable, newline-separated string."""

    return "\n".join(_line(r, theme) for r in rows)
