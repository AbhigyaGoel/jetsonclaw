"""CLAWD-style ASCII banners, the signature mark for a dashboard header.

Returns target-agnostic rows like everything else, so a banner can sit
above widgets and encode to either surface unchanged.
"""

from __future__ import annotations

from .segment import Row, seg
from .theme import Theme

# Block wordmark, hand-aligned. Each glyph is 5 cells wide with a one-cell
# gap, so the whole thing stays phone-PWA friendly and, crucially, spells
# CLAWD correctly.
_CLAWD = (
    "█████ █     █████ █   █ ████ ",
    "█     █     █   █ █   █ █   █",
    "█     █     █████ █ █ █ █   █",
    "█     █     █   █ ██ ██ █   █",
    "█████ █████ █   █ █   █ ████ ",
)


def banner(theme: Theme, subtitle: str | None = None) -> list[Row]:
    """The CLAWD wordmark, plus an optional subtitle line."""

    accent = theme.palette.accent
    rows: list[Row] = [(seg(line, accent, bold=True),) for line in _CLAWD]
    if subtitle:
        rows.append(())
        rows.append((seg(f"{theme.glyphs.sparkle} {subtitle}", theme.palette.muted),))
    return rows
