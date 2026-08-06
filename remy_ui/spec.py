"""Widget specs: the tiny declarative payloads the assistant emits.

The whole latency story rests here. At request time the brain does NOT
generate code, it produces one of these small, validated objects. A
pre-built renderer turns it into pixels. Generating ~200 bytes of spec is
fast; that's what makes "instant" possible.

Specs are frozen dataclasses and validate themselves on construction, so a
malformed spec fails loudly at the boundary instead of rendering garbage.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional

from .text import clean

# Semantic levels a Status can carry.
LEVELS = ("ok", "warn", "bad", "info")


class SpecError(ValueError):
    """Raised when a spec is malformed. Fail fast at the boundary."""


def _opt(text: Optional[str]) -> Optional[str]:
    """Clean an optional free-text field; whitespace-only becomes None."""

    if not text:
        return None
    cleaned = clean(text)
    return cleaned if cleaned.strip() else None


@dataclass(frozen=True)
class Entry:
    """One series in a race: a label and its current value.

    `value` is None while data is still loading, that's the skeleton
    state the renderer draws before the first fetch returns.
    """

    label: str
    value: Optional[float] = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "label", clean(self.label))
        if not self.label.strip():
            raise SpecError("Entry.label must be a non-empty string")
        # Negative is an invalid magnitude (reject). NaN/inf are treated as
        # missing data and render as a placeholder downstream (see numfmt).
        if self.value is not None and self.value < 0:
            raise SpecError(f"Entry.value must be >= 0, got {self.value!r}")


@dataclass(frozen=True)
class RaceBar:
    """A head-to-head percentage-bar widget.

    The canonical example: `Abdul` vs `Stevens`, live. Any two-or-more-way
    contest with numeric values fits, election counts, poll shares, game
    scores, ticker moves.
    """

    kind: str = field(default="comparison", init=False)
    title: str = ""
    entries: tuple[Entry, ...] = ()
    unit: str = "%"                 # shown after each value: "%", "votes", ...
    note: Optional[str] = None      # e.g. "62% reporting" or a timestamp
    as_percent: bool = True         # normalize values to shares of the total

    def __post_init__(self) -> None:
        object.__setattr__(self, "title", clean(self.title))
        object.__setattr__(self, "unit", clean(self.unit))
        object.__setattr__(self, "note", _opt(self.note))
        if not self.title.strip():
            raise SpecError("RaceBar.title must be a non-empty string")
        if len(self.entries) < 2:
            raise SpecError("RaceBar needs at least two entries")
        if not all(isinstance(e, Entry) for e in self.entries):
            raise SpecError("RaceBar.entries must all be Entry instances")

    @property
    def is_loading(self) -> bool:
        """True until every entry has a value, drives the skeleton frame."""

        return any(e.value is None for e in self.entries)

    @property
    def total(self) -> float:
        """Sum of known values; 0 while loading."""

        return sum(e.value for e in self.entries if e.value is not None)


@dataclass(frozen=True)
class Value:
    """A single headline number, optionally with a change and a caption.

    Followers, temperature, price, error rate, steps, any "one number I
    glance at." `delta` colors itself: up is good, down is bad.
    """

    kind: str = field(default="value", init=False)
    title: str = ""
    value: Optional[float] = None
    unit: str = ""
    delta: Optional[float] = None
    caption: Optional[str] = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "title", clean(self.title))
        object.__setattr__(self, "unit", clean(self.unit))
        object.__setattr__(self, "caption", _opt(self.caption))
        if not self.title.strip():
            raise SpecError("Value.title must be a non-empty string")

    @property
    def is_loading(self) -> bool:
        return self.value is None


@dataclass(frozen=True)
class Series:
    """A value over time, drawn as a sparkline. Trends, forecasts, history."""

    kind: str = field(default="series", init=False)
    title: str = ""
    points: tuple[float, ...] = ()
    unit: str = ""
    caption: Optional[str] = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "title", clean(self.title))
        object.__setattr__(self, "unit", clean(self.unit))
        object.__setattr__(self, "caption", _opt(self.caption))
        if not self.title.strip():
            raise SpecError("Series.title must be a non-empty string")
        if len(self.points) < 2:
            raise SpecError("Series needs at least two points")
        if any(p is None for p in self.points):
            raise SpecError("Series.points must all be numbers")


@dataclass(frozen=True)
class Ranking:
    """An ordered leaderboard. Top tracks, top processes, standings, todos."""

    kind: str = field(default="ranking", init=False)
    title: str = ""
    items: tuple[Entry, ...] = ()
    top: Optional[int] = None       # show only the first N after sorting
    caption: Optional[str] = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "title", clean(self.title))
        object.__setattr__(self, "caption", _opt(self.caption))
        if not self.title.strip():
            raise SpecError("Ranking.title must be a non-empty string")
        if not self.items:
            raise SpecError("Ranking needs at least one item")
        if self.top is not None and self.top < 1:
            raise SpecError("Ranking.top must be >= 1")

    @property
    def ordered(self) -> tuple[Entry, ...]:
        """Items sorted high→low, truncated to `top`."""

        ranked = sorted(
            self.items, key=lambda e: (e.value if e.value is not None else -1), reverse=True
        )
        return tuple(ranked[: self.top] if self.top else ranked)


@dataclass(frozen=True)
class Status:
    """A discrete state with a semantic level. Build green/red, up/down, safe."""

    kind: str = field(default="status", init=False)
    title: str = ""
    state: str = ""
    level: str = "info"             # one of LEVELS
    detail: Optional[str] = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "title", clean(self.title))
        object.__setattr__(self, "state", clean(self.state))
        object.__setattr__(self, "detail", _opt(self.detail))
        if not self.title.strip():
            raise SpecError("Status.title must be a non-empty string")
        if not self.state.strip():
            raise SpecError("Status.state must be a non-empty string")
        if self.level not in LEVELS:
            raise SpecError(f"Status.level must be one of {LEVELS}, got {self.level!r}")


@dataclass(frozen=True)
class Gauge:
    """Progress toward a target. Download %, goal, disk, battery, fundraise."""

    kind: str = field(default="gauge", init=False)
    title: str = ""
    value: Optional[float] = None
    target: float = 100.0
    unit: str = ""
    caption: Optional[str] = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "title", clean(self.title))
        object.__setattr__(self, "unit", clean(self.unit))
        object.__setattr__(self, "caption", _opt(self.caption))
        if not self.title.strip():
            raise SpecError("Gauge.title must be a non-empty string")
        if self.target <= 0:
            raise SpecError("Gauge.target must be > 0")
        if self.value is not None and self.value < 0:
            raise SpecError("Gauge.value must be >= 0")

    @property
    def is_loading(self) -> bool:
        return self.value is None

    @property
    def fraction(self) -> float:
        if self.value is None or not math.isfinite(self.value):
            return 0.0
        return max(0.0, min(1.0, self.value / self.target))
