"""Unicode text hygiene: sanitize untrusted strings and measure them in
terminal cells.

Two jobs, both essential for a widget that draws aligned boxes from data it
doesn't control (song titles, calendar text, API strings):

- `clean` strips control characters so a crafted title can't inject terminal
  escapes, and NFC-normalizes so a decomposed accent ("e" + combining mark)
  measures and renders the same as its precomposed form.
- `cell_width` counts how many columns a string occupies on a terminal, not
  how many code points it has. CJK and fullwidth characters take two cells;
  combining marks take zero. `len()` gets both wrong and the box border drifts.
"""

from __future__ import annotations

import unicodedata

# Map C0/C1 control characters out: tab/newline/CR collapse to a space, the
# rest are deleted. Precomputed once; str.translate applies it at C speed.
_CONTROL = {c: None for c in range(0x20)}
_CONTROL.update({c: None for c in range(0x7F, 0xA0)})
_CONTROL.update({0x09: 0x20, 0x0A: 0x20, 0x0D: 0x20})


def clean(text: str) -> str:
    """NFC-normalize and strip control characters from untrusted text."""

    return unicodedata.normalize("NFC", text).translate(_CONTROL)


def _char_cells(ch: str) -> int:
    if unicodedata.combining(ch):
        return 0
    return 2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1


def cell_width(text: str) -> int:
    """Width of `text` in terminal cells (wide = 2, combining = 0)."""

    return sum(_char_cells(ch) for ch in text)


def pad(text: str, width: int) -> str:
    """Right-pad `text` with spaces to `width` terminal cells."""

    return text + " " * max(0, width - cell_width(text))


def truncate(text: str, max_cells: int) -> str:
    """Trim `text` to at most `max_cells` cells, ending with '…' if cut."""

    if max_cells <= 0:
        return ""
    if cell_width(text) <= max_cells:
        return text
    out, used = [], 0
    for ch in text:
        cells = _char_cells(ch)
        if used + cells > max_cells - 1:   # leave one cell for the ellipsis
            break
        out.append(ch)
        used += cells
    return "".join(out) + "…"
