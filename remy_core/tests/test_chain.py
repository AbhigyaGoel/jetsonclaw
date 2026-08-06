"""Chain verb: Judge → Act, gated, with the read step feeding the preview.

    python remy_core/tests/test_chain.py
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from remy_core import RemyContext  # noqa: E402
from remy_core.clients import FakeSpotifyClient  # noqa: E402
from remy_core.router import Router, execute  # noqa: E402

CTX = RemyContext(now=datetime(2026, 8, 5, 14, 0))
R = Router()


def _clients():
    return {"spotify": FakeSpotifyClient()}


def test_playlist_routes_to_chain() -> None:
    intent = R.route("make a playlist of my favorite kanye songs and play it", CTX)
    assert intent.verb == "chain"
    assert intent.params["artist"].lower() == "kanye"
    assert intent.params["play"] is True


def test_playlist_without_play_flag() -> None:
    intent = R.route("make a playlist of my top drake songs", CTX)
    assert intent.verb == "chain"
    assert intent.params["play"] is False


def test_chain_gates_write_until_run() -> None:
    clients = _clients()
    intent = R.route("make a playlist of my favorite kanye and play it", CTX)
    out = execute(intent, CTX, clients)
    # Read step ran (we can preview the tracks) but nothing was written.
    assert out.pending_chain is not None
    assert out.presentation.spec.kind == "ranking"      # the tracks to show
    assert clients["spotify"].playlists == []            # gate held
    assert clients["spotify"].played == []


def test_chain_commits_on_run() -> None:
    clients = _clients()
    intent = R.route("make a playlist of my favorite kanye and play it", CTX)
    out = execute(intent, CTX, clients)
    result = out.pending_chain.run(clients)
    assert result.ok
    assert len(clients["spotify"].playlists) == 1
    playlist = clients["spotify"].playlists[0]
    assert playlist["tracks"][0] == "Runaway"            # real-data ranking preserved
    assert clients["spotify"].played == [playlist["tracks"]]   # played because "play it"
    assert "playing" in result.speech.lower()


def test_chain_confirm_names_count() -> None:
    intent = R.route("make a playlist of my favorite kanye songs", CTX)
    out = execute(intent, CTX, _clients())
    assert "playlist" in out.pending_chain.confirm.lower()
    assert "good?" in out.pending_chain.confirm.lower()


def test_chain_no_tracks_is_graceful() -> None:
    clients = _clients()
    intent = R.route("make a playlist of my favorite taylor swift songs", CTX)
    out = execute(intent, CTX, clients)
    # No Ye-style match → no gate, and running commits nothing.
    assert out.pending_chain.confirm == ""
    result = out.pending_chain.run(clients)
    assert not result.ok
    assert clients["spotify"].playlists == []
    assert "don't see any" in result.speech.lower()


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
