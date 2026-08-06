"""Encode styled rows to an HTML fragment for the web PWA.

Output is a single <pre> so the monospace, box-drawing aesthetic survives
verbatim in the browser, the terminal look *is* the web look. Colors ride
on inline styles per span; the caller can wrap this in whatever panel it
likes. All text is HTML-escaped: never trust label/note content from a feed.
"""

from __future__ import annotations

from html import escape
from typing import Sequence

from ..segment import Row, Segment
from ..theme import Color, Theme


def _hex(color: Color) -> str:
    return f"#{color.r:02x}{color.g:02x}{color.b:02x}"


def _span(seg: Segment, theme: Theme) -> str:
    color = seg.color
    if seg.dim and color is None:
        color = theme.palette.faint
    styles: list[str] = []
    if color is not None:
        styles.append(f"color:{_hex(color)}")
    if seg.bold:
        styles.append("font-weight:600")
    if seg.dim:
        styles.append("opacity:0.85")
    text = escape(seg.text)
    if not styles:
        return text
    return f'<span style="{";".join(styles)}">{text}</span>'


def _line(row: Row, theme: Theme) -> str:
    return "".join(_span(s, theme) for s in row)


def encode(rows: Sequence[Row], theme: Theme) -> str:
    """Join rows into an HTML <pre> fragment."""

    bg = "#1c1b19"
    fg = _hex(theme.palette.text)
    body = "\n".join(_line(r, theme) for r in rows)
    style = (
        f"background:{bg};color:{fg};"
        "font:14px/1.35 'JetBrains Mono','SFMono-Regular',ui-monospace,monospace;"
        "padding:14px 16px;border-radius:10px;margin:0;"
        "white-space:pre;overflow-x:auto"
    )
    return f'<pre class="remy-widget" style="{style}">{body}</pre>'
