"""The `gauge` shape: progress toward a target.

Download %, a fundraising goal, disk usage, battery, steps-toward-10k. One
bar, filled to the fraction of target, with the readout on the right.
"""

from __future__ import annotations

from ..numfmt import human
from ..segment import Row, bar, seg
from ..spec import Gauge
from ..theme import Theme


def build(spec: object, theme: Theme) -> list[Row]:
    if not isinstance(spec, Gauge):
        raise TypeError(f"gauge.build expected Gauge, got {type(spec).__name__}")

    p = theme.palette

    if spec.is_loading:
        readout = "· · ·"
        value_color = p.muted
    else:
        pct = spec.fraction * 100
        unit = f" {spec.unit}" if spec.unit else ""
        readout = f"{human(spec.value)} / {human(spec.target)}{unit} · {pct:.0f}%"
        value_color = p.accent

    row: Row = (
        *bar(spec.fraction, theme.bar_width, p.accent, theme),
        seg("  "),
        seg(readout, value_color, bold=not spec.is_loading),
    )
    rows: list[Row] = [row]
    if spec.caption:
        rows.append((seg(spec.caption, p.muted, dim=True),))
    return rows
