"""Action registry, one entry per effectful capability.

Same pattern as the widget registry and providers/synthesizers: add a file,
add a line. REMY's router matches an intent to a name here.
"""

from __future__ import annotations

from .calendar_add import CalendarAdd
from .create_playlist import CreatePlaylist

ACTIONS = {
    CalendarAdd.name: CalendarAdd(),
    CreatePlaylist.name: CreatePlaylist(),
}
