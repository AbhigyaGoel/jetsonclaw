"""REMY's main loop, end to end: a sentence in, the right verb out.

    python -m remy_core.demo

For each utterance the router decides Tell / Judge / Act with no hard-coded
capability, then it's handled: Tell/Judge render + speak; Act speaks its
confirmation, takes a "yes", and runs. Everything is against fake clients.
This is the seam REMY's wake-word + Whisper feed in production.
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # for remy_ui

from remy_ui import CLAWD, to_terminal  # noqa: E402

from . import RemyContext  # noqa: E402
from .clients import FakeCalendarClient, FakeSpotifyClient  # noqa: E402
from .router import Router, execute  # noqa: E402

CTX = RemyContext(now=datetime(2026, 8, 5, 14, 0), calendars={"school": "abhigyag@usc.edu"})
CLIENTS = {"spotify": FakeSpotifyClient(), "calendar": FakeCalendarClient()}

TRANSCRIPT = [
    "what have I been listening to lately",
    "my favorite Kanye songs",
    "add dinner with friends friday at 8pm",
    "put office hours tuesday 3 to 4pm on my school calendar",
    "make a playlist of my favorite Kanye and play it",   # Chain: Judge → Act
    "my top 3 drake songs",
    "what's the weather in tokyo",          # nothing local handles it
]

MUTED = "\x1b[38;2;138;133;120m"
OFF = "\x1b[0m"


def _panel(spec) -> str:
    return "\n".join("    " + line for line in to_terminal(spec, CLAWD).splitlines())


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    router = Router()
    for utterance in TRANSCRIPT:
        print(f"\n{MUTED}» “{utterance}”{OFF}")
        intent = router.route(utterance, CTX)
        if intent is None:
            print(f"  « I can't do that one yet.  {MUTED}(→ local model fallback){OFF}")
            continue

        out = execute(intent, CTX, CLIENTS)
        tag = f"{MUTED}[{intent.verb}]{OFF}"
        if out.pending is not None:                    # Act
            print(f"  « {out.pending.confirm}  {tag}")
            print("  » yes")
            result = out.pending.run(CLIENTS["calendar"])
            print(f"  « {result.speech}")
        elif out.pending_chain is not None:            # Chain (read shown, write gated)
            if out.presentation is not None:
                print(f"  {MUTED}(showing what it'll use){OFF}\n")
                print(_panel(out.presentation.spec))
            print(f"\n  « {out.pending_chain.confirm}  {tag}")
            print("  » yes")
            result = out.pending_chain.run(CLIENTS)
            print(f"  « {result.speech}")
        else:                                          # Tell / Judge
            print(f"  « {out.presentation.speech}  {tag}\n")
            print(_panel(out.presentation.spec))


if __name__ == "__main__":
    main()
