"""Top Hacker News stories, stdlib only."""

import json
import urllib.request

API = "https://hacker-news.firebaseio.com/v0"


def _get(path: str):
    with urllib.request.urlopen(f"{API}/{path}.json", timeout=10) as resp:
        return json.loads(resp.read())


def handle(text: str) -> str:
    ids = _get("topstories")[:3]
    titles = [_get(f"item/{i}").get("title", "untitled") for i in ids]
    return "Top of Hacker News: " + ". ".join(
        f"{n}. {t}" for n, t in enumerate(titles, 1))


def selftest() -> str:
    assert _get("topstories"), "HN API returned nothing"
    return "ok"
