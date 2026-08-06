"""Speak a spec.

Every shape has two outputs: a renderer (to the screen) and a verbalizer
(to Piper). Because REMY is a voice assistant, the same spec that paints a
panel also produces the sentence it says out loud. `shape → (render | speak)`
is the spine of the whole framework, this module is the `speak` half.

Verbalizers return plain, TTS-friendly text: no glyphs, no commas in
numbers, natural phrasing.
"""

from __future__ import annotations

from typing import Callable

from .numfmt import spoken
from .spec import Gauge, Ranking, RaceBar, Series, Status, Value


def _comparison(spec: RaceBar) -> str:
    if spec.is_loading:
        return f"Still waiting on {spec.title}."
    ranked = sorted(
        spec.entries, key=lambda e: e.value if e.value is not None else -1, reverse=True
    )
    lead, second = ranked[0], ranked[1]
    if spec.as_percent and spec.total > 0:
        lp = lead.value / spec.total * 100
        sp = second.value / spec.total * 100
        return f"{lead.label} leads with {lp:.0f} percent, {second.label} at {sp:.0f}."
    return f"{lead.label} leads {second.label}, {spoken(lead.value)} to {spoken(second.value)}."


def _value(spec: Value) -> str:
    if spec.is_loading:
        return f"No reading yet for {spec.title}."
    unit = f" {spec.unit}" if spec.unit else ""
    base = f"{spec.title}: {spoken(spec.value)}{unit}"
    if spec.delta is not None:
        direction = "up" if spec.delta > 0 else "down" if spec.delta < 0 else "flat"
        return f"{base}, {direction} {spoken(abs(spec.delta))}."
    return f"{base}."


def _series(spec: Series) -> str:
    first, last = spec.points[0], spec.points[-1]
    trend = "up" if last > first else "down" if last < first else "flat"
    unit = f" {spec.unit}" if spec.unit else ""
    return f"{spec.title}: now {spoken(last)}{unit}, trending {trend} over the last {len(spec.points)}."


def _ranking(spec: Ranking) -> str:
    items = spec.ordered
    lead = items[0]
    if len(items) == 1:
        return f"{spec.title}: {lead.label}."
    return f"Top {spec.title}: {lead.label}, then {items[1].label}."


def _status(spec: Status) -> str:
    detail = f", {spec.detail}" if spec.detail else ""
    return f"{spec.title}: {spec.state}{detail}."


def _gauge(spec: Gauge) -> str:
    if spec.is_loading:
        return f"No reading yet for {spec.title}."
    pct = spec.fraction * 100
    unit = f" {spec.unit}" if spec.unit else ""
    return f"{spec.title}: {spoken(spec.value)} of {spoken(spec.target)}{unit}, {pct:.0f} percent."


VERBALIZERS: dict[str, Callable[[object], str]] = {
    "comparison": _comparison,
    "value": _value,
    "series": _series,
    "ranking": _ranking,
    "status": _status,
    "gauge": _gauge,
}


def to_speech(spec: object) -> str:
    """Turn a spec into a sentence for TTS."""

    kind = getattr(spec, "kind", None)
    verbalizer = VERBALIZERS.get(kind)
    if verbalizer is None:
        raise ValueError(f"No verbalizer registered for kind {kind!r}")
    return verbalizer(spec)
