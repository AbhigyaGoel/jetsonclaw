"""The router: utterance → intent → outcome.

Two stages, deliberately split:

  route(utterance, ctx)              → Intent | None   (pure decision, no I/O)
  execute(intent, ctx, clients)      → Outcome         (runs it)

`route` is side-effect-free and deterministic, so intent classification is
trivially testable. `execute` is where clients get touched, and where the
Act path stops at a `Pending` (needs a spoken yes) while Tell/Judge return a
ready `Presentation`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from ..capability import Pending, PendingChain, Presentation, plan
from ..context import RemyContext
from .rules import ROUTES, Route


@dataclass(frozen=True)
class Intent:
    """What the router decided: which capability, which verb, which params."""

    capability: Any
    verb: str                    # "tell" | "judge" | "act"
    method: str                  # "fetch" | "derive" | ""
    client_key: Optional[str]
    params: dict
    utterance: str


@dataclass(frozen=True)
class Outcome:
    """The result of executing an intent. One primary payload is set.

    - Tell/Judge → `presentation` (render + speak now).
    - Act → `pending` (speak `pending.confirm`, await yes, then `pending.run`).
    - Chain → `pending_chain` (read step already ran into `presentation`;
      speak `.confirm`, await yes, then `.run(clients)`).
    """

    verb: str
    presentation: Optional[Presentation] = None
    pending: Optional[Pending] = None
    pending_chain: Optional[PendingChain] = None


class Router:
    def __init__(self, routes: list[Route] = ROUTES) -> None:
        self._routes = routes

    def route(self, utterance: str, ctx: RemyContext) -> Optional[Intent]:
        """First matching route wins. None means 'nothing local handled it'."""

        for r in self._routes:
            params = r.match(utterance, ctx)
            if params is not None:
                return Intent(
                    capability=r.capability,
                    verb=r.verb,
                    method=r.method,
                    client_key=r.client_key,
                    params=params,
                    utterance=utterance,
                )
        return None


def execute(intent: Intent, ctx: RemyContext, clients: dict) -> Outcome:
    """Run a decided intent against the relevant backend client(s)."""

    if intent.verb == "act":
        # Actions self-parse and stop at a confirmation gate.
        pending = plan(intent.capability, intent.utterance, ctx)
        return Outcome(verb="act", pending=pending)

    if intent.verb == "chain":
        # The chain runs its read steps now and gates only the write step.
        pc = intent.capability.gather(intent.params, ctx, clients)
        return Outcome(verb="chain", pending_chain=pc, presentation=pc.show)

    client = clients.get(intent.client_key)
    method = getattr(intent.capability, intent.method)
    presentation = method(intent.params, ctx, client)
    return Outcome(verb=intent.verb, presentation=presentation)


__all__ = ["Router", "Intent", "Outcome", "execute"]
