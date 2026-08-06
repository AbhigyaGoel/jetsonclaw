"""Widget registry, one entry per data shape.

Each widget lives in its own module and exposes a `build(spec, theme)`
function returning target-agnostic rows. Adding a shape = adding a file and
one registry line. The registry is keyed by the spec's `kind`, which is the
shape name (`value`, `comparison`, ...), widgets are typed by the shape of
information, never by domain.
"""

from __future__ import annotations

from typing import Callable, Sequence

from ..segment import Row
from ..theme import Theme
from . import gauge, race_bar, ranking, series, status, value

BUILDERS: dict[str, Callable[[object, Theme], Sequence[Row]]] = {
    "value": value.build,
    "comparison": race_bar.build,
    "series": series.build,
    "ranking": ranking.build,
    "status": status.build,
    "gauge": gauge.build,
}
