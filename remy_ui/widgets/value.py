"""The `value` shape: one headline number with an optional change.

The glance widget, followers, temperature, price, steps, error rate. The
delta colors itself by direction so meaning reads at a glance.
"""

from __future__ import annotations

from ..numfmt import human, signed
from ..segment import Row, seg
from ..spec import Value
from ..theme import Theme, delta_color


def build(spec: object, theme: Theme) -> list[Row]:
    if not isinstance(spec, Value):
        raise TypeError(f"value.build expected Value, got {type(spec).__name__}")

    p = theme.palette
    g = theme.glyphs

    if spec.value is None:
        headline: Row = (seg("· · ·", p.muted),)
    else:
        parts = [seg(human(spec.value), p.accent, bold=True)]
        if spec.unit:
            parts.append(seg(f" {spec.unit}", p.muted))
        if spec.delta is not None:
            arrow = g.up if spec.delta > 0 else g.down if spec.delta < 0 else g.flat
            color = delta_color(theme, spec.delta)
            parts.append(seg("   "))
            parts.append(seg(f"{arrow} {signed(spec.delta)}", color, bold=True))
        headline = tuple(parts)

    rows: list[Row] = [headline]
    if spec.caption:
        rows.append((seg(spec.caption, p.muted, dim=True),))
    return rows
