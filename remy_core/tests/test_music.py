"""Tell + Judge planes over Spotify: top tracks and favorite-by-artist.

    python remy_core/tests/test_music.py
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from remy_core import RemyContext  # noqa: E402
from remy_core.clients import FakeSpotifyClient  # noqa: E402
from remy_core.providers import PROVIDERS  # noqa: E402
from remy_core.synthesizers import SYNTHESIZERS  # noqa: E402

CTX = RemyContext(now=datetime(2026, 8, 5, 14, 0))
CLIENT = FakeSpotifyClient()
TOP = PROVIDERS["spotify.top_tracks"]
FAV = SYNTHESIZERS["spotify.favorite_by_artist"]


def test_top_tracks_returns_ranking() -> None:
    pres = TOP.fetch({"window": "medium", "limit": 5}, CTX, CLIENT)
    assert pres.spec.kind == "ranking"
    assert len(pres.spec.items) == 5
    assert "most-played" in pres.speech.lower()


def test_top_tracks_ordered_by_plays() -> None:
    pres = TOP.fetch({"limit": 5}, CTX, CLIENT)
    values = [e.value for e in pres.spec.ordered]
    assert values == sorted(values, reverse=True)   # highest plays first


def test_favorite_kanye_filters_to_artist() -> None:
    pres = FAV.derive({"artist": "Kanye", "limit": 5}, CTX, CLIENT)
    labels = [e.label for e in pres.spec.items]
    # Every returned track must be a Ye track from the catalog.
    kanye_titles = {"Runaway", "Stronger", "Power", "Flashing Lights", "Gold Digger", "Bound 2", "Heartless"}
    assert set(labels).issubset(kanye_titles)
    assert len(labels) == 5


def test_favorite_ranked_by_real_plays() -> None:
    pres = FAV.derive({"artist": "ye"}, CTX, CLIENT)
    # Runaway (512) is the top Ye track in the catalog → it leads.
    assert pres.spec.ordered[0].label == "Runaway"
    assert "Runaway" in pres.speech


def test_alias_resolves() -> None:
    a = FAV.derive({"artist": "Kanye West"}, CTX, CLIENT).spec.items
    b = FAV.derive({"artist": "ye"}, CTX, CLIENT).spec.items
    assert [e.label for e in a] == [e.label for e in b]


def test_unknown_artist_is_graceful() -> None:
    pres = FAV.derive({"artist": "Taylor Swift"}, CTX, CLIENT)
    assert pres.spec.kind == "status"
    assert "don't see any" in pres.speech.lower()


def test_presentation_speaks_and_renders() -> None:
    from remy_ui import to_html, to_speech

    pres = TOP.fetch({}, CTX, CLIENT)
    assert "<pre" in to_html(pres.spec)
    assert to_speech(pres.spec)          # the shape is verbalizable too
    assert pres.speech.endswith(".")


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
