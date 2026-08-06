"""Render dispatch: spec -> rows -> a chosen surface.

The public entry points. Callers hand in a spec and get back a string ready
for the surface they name. The two-stage pipeline (build rows, then encode)
is what lets the TUI and the web PWA share every widget.
"""

from __future__ import annotations

from ..frame import frame
from ..segment import Row
from ..theme import CLAWD, Theme
from ..widgets import BUILDERS
from . import html as _html
from . import terminal as _terminal


def _build(spec: object, theme: Theme, min_width: int) -> list[Row]:
    """Resolve a spec to its framed rows."""

    kind = getattr(spec, "kind", None)
    builder = BUILDERS.get(kind)
    if builder is None:
        raise ValueError(f"No widget registered for kind {kind!r}")
    rows = list(builder(spec, theme))
    return frame(getattr(spec, "title", ""), rows, theme, min_width)


def to_terminal(spec: object, theme: Theme = CLAWD, min_width: int = 0) -> str:
    """Render a spec to an ANSI string for the TUI.

    Pass a shared `min_width` to align a group of related panels.
    """

    return _terminal.encode(_build(spec, theme, min_width), theme)


def to_html(spec: object, theme: Theme = CLAWD, min_width: int = 0) -> str:
    """Render a spec to an HTML fragment for the web dashboard."""

    return _html.encode(_build(spec, theme, min_width), theme)


__all__ = ["to_terminal", "to_html"]
