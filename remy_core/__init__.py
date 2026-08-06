"""remy_core: REMY's capability layer, the verbs beyond talking.

    Provider     reads data, returns a shape         (Tell)
    Synthesizer  ranks your own data, no guessing     (Judge)
    Action       causes an effect, gated by a yes     (Act)

    plus Chain, which sequences the above behind one gate.

The router picks the verb from a spoken line; see remy_core.router. An Action
is the load-bearing pattern: it splits into parse, preview, and execute, so a
confirmation always sits between intent and effect.

    from datetime import datetime
    from remy_core import RemyContext, plan
    from remy_core.actions import ACTIONS
    from remy_core.clients import FakeCalendarClient

    ctx = RemyContext(now=datetime(2026, 8, 5, 14, 0))
    pending = plan(ACTIONS["calendar.add"], "dinner with j fri at 8pm", ctx)
    pending.confirm                      # REMY says this, waits for "yes"
    pending.run(FakeCalendarClient())    # only after confirmation
"""

from __future__ import annotations

from .capability import (
    Action,
    ActionError,
    Pending,
    PendingChain,
    Presentation,
    Provider,
    Result,
    Synthesizer,
    plan,
)
from .context import RemyContext

__all__ = [
    "RemyContext",
    "Action",
    "ActionError",
    "Pending",
    "PendingChain",
    "Result",
    "Presentation",
    "Provider",
    "Synthesizer",
    "plan",
]
