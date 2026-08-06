"""remy_ui: a spec-driven widget and voice framework in the CLAWD aesthetic.

The framework knows *shapes of information*, never topics. Weather, fitness,
DevOps, music are all just data in one of a small closed set of shapes; each
shape has a widget (to draw) and a verbalizer (to speak).

    spec  (a small frozen dataclass, one of the shapes below)
      │
      ├─► render.to_terminal()  ANSI for the TUI
      ├─► render.to_html()      a <pre> fragment for the web PWA
      └─► verbalize.to_speech() a sentence for Piper TTS

The heavy work is all here, at build time. A request just fills in a spec.

Shapes:
    Value       one headline number (+ optional delta)
    RaceBar     a comparison, things measured against each other
    Series      a value over time, as a sparkline
    Ranking     an ordered leaderboard
    Status      a discrete state with a semantic level
    Gauge       progress toward a target
"""

from __future__ import annotations

from .render import to_html, to_terminal
from .spec import (
    Entry,
    Gauge,
    Ranking,
    RaceBar,
    Series,
    SpecError,
    Status,
    Value,
)
from .theme import CLAWD, Theme
from .verbalize import to_speech

__all__ = [
    # shapes
    "Value",
    "RaceBar",
    "Series",
    "Ranking",
    "Status",
    "Gauge",
    "Entry",
    "SpecError",
    # theme
    "Theme",
    "CLAWD",
    # outputs
    "to_terminal",
    "to_html",
    "to_speech",
]
