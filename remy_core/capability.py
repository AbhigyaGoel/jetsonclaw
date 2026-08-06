"""The capability layer: the three verbs REMY has beyond talking.

    Provider     reads data      → returns a shape (Tell)
    Synthesizer  data + memory   → a derived answer (Judge)
    Action       causes an effect, gated by a spoken yes (Act)

This module defines the Action contract and its confirm-gated driver, since
that's the plane calendar-add exercises. Provider/Synthesizer are declared
here as the sibling shapes of the same idea; their concrete forms come next.

The whole point: an Action never fires on its own. REMY `plan()`s it, speaks
the `confirm` line, waits for "yes", then `run()`s the pending plan. The gate
is structural, not a convention someone might forget.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional, Protocol

from .context import RemyContext


class ActionError(ValueError):
    """Raised when an utterance can't be turned into a runnable action.

    The message is user-facing, REMY speaks it ("I couldn't tell when,
    try 'friday at 8pm'"), so it must be a helpful, spoken-friendly hint.
    """


@dataclass(frozen=True)
class Result:
    """The outcome of running an action. Drives both speech and screen."""

    ok: bool
    speech: str                 # what REMY says out loud
    detail: str = ""            # a secondary line for the panel
    data: dict = field(default_factory=dict)   # raw effect data (ids, links)


@dataclass(frozen=True)
class Presentation:
    """What a Provider or Synthesizer returns: a shape to draw + words to say.

    `spec` is a remy_ui shape (Ranking, Value, ...). This is the seam where the
    capability layer hands off to the render/speak tail, the caller renders
    `spec` to the screen and speaks `speech`.
    """

    spec: Any                   # a remy_ui shape spec
    speech: str                 # what REMY says out loud


class Provider(Protocol):
    """Reads data and returns it as a shape. The Tell verb. No side effects."""

    name: str

    def fetch(self, params: dict, ctx: RemyContext, client: Any) -> Presentation:
        """Query a source and shape the result."""


class Synthesizer(Protocol):
    """Derives an answer from data + memory. The Judge verb.

    Real-data-only by design: a Synthesizer filters, ranks, and aggregates
    the user's own data. It does not invent taste, any judgment is grounded
    in something the data actually says.
    """

    name: str

    def derive(self, params: dict, ctx: RemyContext, client: Any) -> Presentation:
        """Turn source data into a grounded, derived answer."""


class Action(Protocol):
    """A capability that changes the world. Parse, preview, execute, split
    so the confirmation gate can sit cleanly between preview and execute."""

    name: str

    def parse(self, utterance: str, ctx: RemyContext) -> Any:
        """Utterance → validated params. Raises ActionError on failure."""

    def preview(self, params: Any, ctx: RemyContext) -> str:
        """The spoken confirmation question for these params."""

    def execute(self, params: Any, client: Any) -> Result:
        """Perform the effect against an injected client."""


@dataclass(frozen=True)
class Pending:
    """A parsed, previewed action awaiting a yes. Nothing has happened yet."""

    action: Action
    params: Any
    confirm: str

    def run(self, client: Any) -> Result:
        """Commit the effect. Call only after the user has confirmed."""

        return self.action.execute(self.params, client)


def plan(action: Action, utterance: str, ctx: RemyContext) -> Pending:
    """Turn an utterance into a Pending action + its confirmation line.

    This does the parse and the preview but *not* the effect, so REMY can
    ask before doing. Raises ActionError if the utterance can't be parsed.
    """

    params = action.parse(utterance, ctx)
    return Pending(action=action, params=params, confirm=action.preview(params, ctx))


@dataclass(frozen=True)
class PendingChain:
    """A composed capability: its read steps have already run (to build the
    confirmation and the preview), and only its write step awaits a yes.

    `confirm == ""` means there's nothing to gate (e.g. the read step found
    nothing), the caller just shows `show` and speaks, no question asked.
    `show` is the read step's Presentation, so REMY can display what it's
    about to act on *while* asking.
    """

    confirm: str
    _commit: Any                            # Callable[[dict], Result]
    show: Optional[Presentation] = None

    def run(self, clients: dict) -> Result:
        """Commit the write step against the client bundle. After the yes."""

        return self._commit(clients)
