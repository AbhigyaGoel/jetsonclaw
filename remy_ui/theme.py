"""Visual theme: the Claude Code / CLAWD aesthetic as data.

Everything the look depends on lives here as immutable constants, palette,
glyphs, and box-drawing characters. Change the feel of every widget by
editing this one file. Nothing else hardcodes a color or a glyph.
"""

from __future__ import annotations

from typing import NamedTuple


class Color(NamedTuple):
    """A 24-bit RGB color. Immutable by construction."""

    r: int
    g: int
    b: int


class Palette(NamedTuple):
    """The colors that define the aesthetic. Warm, earthy, terminal-native."""

    # Claude's signature terracotta, the primary accent.
    accent: Color = Color(217, 119, 87)      # #D97757
    # Foreground text on a dark terminal: warm cream, not pure white.
    text: Color = Color(232, 228, 216)       # #E8E4D8
    # Secondary / label text: muted sand.
    muted: Color = Color(138, 133, 120)      # #8A8578
    # Box borders and skeleton fills: dim.
    faint: Color = Color(90, 86, 78)         # #5A564E

    # Semantic colors, shared by every shape so meaning stays consistent:
    # good/up, bad/down, caution, and neutral info.
    pos: Color = Color(127, 163, 127)        # sage, good / rising
    neg: Color = Color(198, 93, 78)          # warm red, bad / falling
    warn: Color = Color(199, 168, 96)        # ochre, caution
    info: Color = Color(108, 142, 191)       # slate, neutral

    # The cycle used to color distinct series (candidates, teams, tickers).
    # Warm-led and deliberately earthy so multi-series still reads on-brand.
    series: tuple[Color, ...] = (
        Color(217, 119, 87),   # terracotta
        Color(108, 142, 191),  # slate blue
        Color(127, 163, 127),  # sage
        Color(155, 126, 189),  # muted violet
        Color(199, 168, 96),   # ochre
    )


class Glyphs(NamedTuple):
    """The characters the widgets draw with."""

    # Rounded box corners, matches Claude Code's panels.
    top_left: str = "╭"      # ╭
    top_right: str = "╮"     # ╮
    bottom_left: str = "╰"   # ╰
    bottom_right: str = "╯"  # ╯
    horizontal: str = "─"    # ─
    vertical: str = "│"      # │

    # Bar fills.
    bar_full: str = "█"      # █
    bar_empty: str = "░"     # ░

    # Sparkline ramp, eight levels low→high.
    spark: tuple = tuple("▁▂▃▄▅▆▇█")

    # Trend and status marks.
    up: str = "▲"
    down: str = "▼"
    flat: str = "▬"
    dot: str = "●"

    # Claude's sparkle, the signature mark in headers.
    sparkle: str = "✻"       # ✻


class Theme(NamedTuple):
    """A complete theme: palette + glyphs + a couple of layout knobs."""

    palette: Palette = Palette()
    glyphs: Glyphs = Glyphs()
    bar_width: int = 34   # cells of bar per race entry
    pad: int = 1          # inner horizontal padding inside boxes


# The default theme, ready to import and use.
CLAWD = Theme()


def series_color(theme: Theme, index: int) -> Color:
    """Pick a stable series color by position, cycling if needed."""

    series = theme.palette.series
    return series[index % len(series)]


def level_color(theme: Theme, level: str) -> Color:
    """Map a semantic level name to its color. Defaults to neutral info."""

    p = theme.palette
    return {"ok": p.pos, "bad": p.neg, "warn": p.warn, "info": p.info}.get(level, p.info)


def delta_color(theme: Theme, delta: float) -> Color:
    """Color a change: positive good, negative bad, zero neutral."""

    if delta > 0:
        return theme.palette.pos
    if delta < 0:
        return theme.palette.neg
    return theme.palette.muted
