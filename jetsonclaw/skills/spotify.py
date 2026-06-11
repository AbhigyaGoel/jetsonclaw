"""Spotify skill: playback control, track search, and playlist playback.

Web API with OAuth tokens at ~/spotify_tokens.json (access + refresh +
client creds). All calls run in a thread via asyncio.to_thread — stdlib only.
"""

from __future__ import annotations

import asyncio
import base64
import json
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from ..config import SpotifyConfig
from ..router.intents import Intent

API = "https://api.spotify.com/v1"


class SpotifyError(Exception):
    pass


class SpotifyClient:
    def __init__(self, token_file: str) -> None:
        self._token_file = Path(token_file).expanduser()

    def configured(self) -> bool:
        return self._token_file.is_file()

    # --- token handling ---

    def _load_tokens(self) -> dict:
        try:
            with open(self._token_file) as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            raise SpotifyError(f"no spotify tokens at {self._token_file}") from e

    def _refresh(self, tokens: dict) -> dict:
        auth = base64.b64encode(
            f"{tokens['client_id']}:{tokens['client_secret']}".encode()
        ).decode()
        data = urllib.parse.urlencode({
            "grant_type": "refresh_token",
            "refresh_token": tokens["refresh_token"],
        }).encode()
        req = urllib.request.Request(
            "https://accounts.spotify.com/api/token", data=data,
            headers={"Authorization": f"Basic {auth}",
                     "Content-Type": "application/x-www-form-urlencoded"},
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read().decode())
        updated = {**tokens, "access_token": result["access_token"]}
        if "refresh_token" in result:
            updated["refresh_token"] = result["refresh_token"]
        with open(self._token_file, "w") as f:
            json.dump(updated, f, indent=2)
        return updated

    # --- generic request ---

    def request(self, method: str, path: str, body: dict | None = None,
                params: dict | None = None, retry: bool = True) -> dict:
        tokens = self._load_tokens()
        url = f"{API}{path}"
        if params:
            url += "?" + urllib.parse.urlencode(params)
        data = json.dumps(body).encode() if body is not None else None
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}
        if data is not None:
            headers["Content-Type"] = "application/json"
        elif method in ("POST", "PUT"):
            headers["Content-Length"] = "0"
        req = urllib.request.Request(url, method=method, data=data, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                if resp.status == 204:
                    return {}
                raw = resp.read().decode()
                return json.loads(raw) if raw else {}
        except urllib.error.HTTPError as e:
            if e.code == 401 and retry:
                self._refresh(tokens)
                return self.request(method, path, body, params, retry=False)
            if e.code == 404:
                raise SpotifyError("no active Spotify device — open Spotify somewhere") from e
            if e.code == 403:
                raise SpotifyError("Spotify refused (missing scope or Premium?)") from e
            raise SpotifyError(f"Spotify HTTP {e.code}") from e
        except urllib.error.URLError as e:
            raise SpotifyError(f"Spotify unreachable: {e.reason}") from e


class SpotifySkill:
    def __init__(self, cfg: SpotifyConfig) -> None:
        self._client = SpotifyClient(cfg.token_file)

    def configured(self) -> bool:
        return self._client.configured()

    async def handle(self, intent: Intent) -> str:
        try:
            return await asyncio.to_thread(self._dispatch, intent)
        except SpotifyError as e:
            return str(e)

    def _dispatch(self, intent: Intent) -> str:
        c = self._client
        if intent.name == "spotify.next":
            c.request("POST", "/me/player/next")
            return "Skipped."
        if intent.name == "spotify.pause":
            c.request("PUT", "/me/player/pause")
            return "Paused."
        if intent.name == "spotify.resume":
            c.request("PUT", "/me/player/play")
            return "Resuming."
        if intent.name == "spotify.volume_set":
            return self._set_volume(int(intent.slots["percent"]))
        if intent.name == "spotify.volume_delta":
            return self._nudge_volume(int(intent.slots["delta"]))
        if intent.name == "spotify.now_playing":
            return self._now_playing()
        if intent.name == "spotify.play_track":
            return self._play_track(intent.slots["query"])
        if intent.name == "spotify.play_playlist":
            return self._play_playlist(intent.slots["name"])
        return "I don't know that Spotify command."

    def _set_volume(self, percent: int) -> str:
        percent = max(0, min(100, percent))
        self._client.request("PUT", "/me/player/volume",
                             params={"volume_percent": percent})
        return f"Volume {percent}."

    def _nudge_volume(self, delta: int) -> str:
        state = self._client.request("GET", "/me/player")
        current = (state.get("device") or {}).get("volume_percent")
        if current is None:
            return "No active device to adjust."
        return self._set_volume(current + delta)

    def _now_playing(self) -> str:
        data = self._client.request("GET", "/me/player/currently-playing")
        item = data.get("item") if data else None
        if not item:
            return "Nothing's playing right now."
        artist = item["artists"][0]["name"] if item.get("artists") else "unknown"
        return f"{item['name']} by {artist}."

    def _play_track(self, query: str) -> str:
        data = self._client.request("GET", "/search",
                                    params={"q": query, "type": "track", "limit": 1})
        tracks = data.get("tracks", {}).get("items", [])
        if not tracks:
            return f"Couldn't find '{query}' on Spotify."
        track = tracks[0]
        self._client.request("PUT", "/me/player/play", body={"uris": [track["uri"]]})
        artist = track["artists"][0]["name"] if track.get("artists") else ""
        return f"Playing {track['name']} by {artist}."

    def _play_playlist(self, name: str) -> str:
        data = self._client.request("GET", "/me/playlists", params={"limit": 50})
        playlists = data.get("items", [])
        wanted = name.lower()
        match = next((p for p in playlists if wanted in p["name"].lower()), None)
        if match is None:
            names = ", ".join(p["name"] for p in playlists[:5]) or "none found"
            return f"No playlist matching '{name}'. You have: {names}."
        self._client.request("PUT", "/me/player/play", body={"context_uri": match["uri"]})
        return f"Playing your playlist {match['name']}."
