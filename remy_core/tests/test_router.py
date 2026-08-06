"""Router: does an utterance land on the right verb + params, and execute.

    python remy_core/tests/test_router.py
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from remy_core import RemyContext  # noqa: E402
from remy_core.clients import FakeCalendarClient, FakeSpotifyClient  # noqa: E402
from remy_core.router import Router, execute  # noqa: E402

CTX = RemyContext(now=datetime(2026, 8, 5, 14, 0), calendars={"school": "abhigyag@usc.edu"})
CLIENTS = {"spotify": FakeSpotifyClient(), "calendar": FakeCalendarClient()}
R = Router()


def test_favorite_artist_routes_to_judge() -> None:
    intent = R.route("what are my favorite kanye songs", CTX)
    assert intent.verb == "judge"
    assert intent.params["artist"].lower() == "kanye"


def test_top_tracks_routes_to_tell() -> None:
    intent = R.route("what have I been listening to lately", CTX)
    assert intent.verb == "tell"
    assert intent.params["window"] == "short"     # "lately"


def test_window_extraction() -> None:
    assert R.route("my top tracks of all time", CTX).params["window"] == "long"
    assert R.route("top tracks these past few months", CTX).params["window"] == "medium"


def test_limit_extraction() -> None:
    assert R.route("my top 10 tracks", CTX).params["limit"] == 10


def test_add_event_routes_to_act() -> None:
    intent = R.route("add dinner with friends friday at 8pm", CTX)
    assert intent.verb == "act"


def test_favorite_beats_top_ordering() -> None:
    # Contains "top" but names an artist → Judge, not Tell.
    intent = R.route("my top drake songs", CTX)
    assert intent.verb == "judge"
    assert intent.params["artist"].lower() == "drake"


def test_add_without_time_is_unhandled() -> None:
    # "add milk" has no when → not a calendar event → nothing local matches.
    assert R.route("add milk to the list", CTX) is None


def test_unhandled_returns_none() -> None:
    assert R.route("what's the meaning of life", CTX) is None


def test_execute_judge_returns_presentation() -> None:
    intent = R.route("my favorite kanye songs", CTX)
    out = execute(intent, CTX, CLIENTS)
    assert out.presentation is not None
    assert out.presentation.spec.ordered[0].label == "Runaway"
    assert out.pending is None


def test_execute_act_returns_pending_unrun() -> None:
    client = FakeCalendarClient()
    intent = R.route("add gym tomorrow at 7am", CTX)
    out = execute(intent, CTX, {"calendar": client})
    assert out.pending is not None
    assert client.created == []                  # gate held: not run yet
    result = out.pending.run(client)             # confirm → run
    assert result.ok and len(client.created) == 1


def _run_all() -> int:
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failed = 0
    for t in tests:
        try:
            t()
            print(f"  ok  {t.__name__}")
        except Exception as exc:  # noqa: BLE001
            failed += 1
            print(f"FAIL  {t.__name__}: {exc}")
    print(f"\n{len(tests) - failed}/{len(tests)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(_run_all())
