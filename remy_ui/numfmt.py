"""Small number-formatting helpers shared by widgets and verbalizers.

Keeping this in one place means every shape formats numbers the same way,
thousands separators on screen, spoken-friendly rounding for the voice.
"""

from __future__ import annotations


def human(x: float) -> str:
    """A compact, thousands-separated form. Whole numbers drop the decimal."""

    if x == int(x):
        return f"{int(x):,}"
    return f"{x:,.2f}".rstrip("0").rstrip(".")


def signed(x: float) -> str:
    """Like `human`, but always shows the sign, for deltas."""

    sign = "+" if x >= 0 else "-"
    return f"{sign}{human(abs(x))}"


def spoken(x: float) -> str:
    """A rounded, comma-free form suitable for TTS ('1200' not '1,200')."""

    if x == int(x):
        return str(int(x))
    return f"{x:.1f}"
