"""Spotify OAuth via a 127.0.0.1 loopback redirect.

Spotify stopped accepting `localhost` and raw LAN-IP redirect URIs in 2025; a
loopback flow must use the literal `127.0.0.1`. This helper runs a one-shot
loopback server, walks the owner through consent, exchanges the code, and writes
tokens in the exact shape skills/spotify.py reads (~/spotify_tokens.json).

Stdlib only, matching the Spotify skill. Register this redirect URI in the
Spotify app dashboard first:  http://127.0.0.1:8888/callback
"""

from __future__ import annotations

import base64
import json
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

REDIRECT_HOST = "127.0.0.1"
DEFAULT_PORT = 8888
AUTH_URL = "https://accounts.spotify.com/authorize"
TOKEN_URL = "https://accounts.spotify.com/api/token"

# Everything the playback skill needs: control, read state, read private lists.
SCOPES = (
    "user-modify-playback-state",
    "user-read-playback-state",
    "user-read-currently-playing",
    "playlist-read-private",
)


def redirect_uri(port: int = DEFAULT_PORT) -> str:
    """The loopback redirect Spotify requires — 127.0.0.1, never localhost."""
    return f"http://{REDIRECT_HOST}:{port}/callback"


def authorize_url(client_id: str, port: int = DEFAULT_PORT,
                  scopes: tuple[str, ...] = SCOPES, state: str = "remy") -> str:
    query = urllib.parse.urlencode({
        "client_id": client_id,
        "response_type": "code",
        "redirect_uri": redirect_uri(port),
        "scope": " ".join(scopes),
        "state": state,
    })
    return f"{AUTH_URL}?{query}"


def exchange_code(client_id: str, client_secret: str, code: str,
                  port: int = DEFAULT_PORT) -> dict:
    auth = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    data = urllib.parse.urlencode({
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri(port),
    }).encode()
    req = urllib.request.Request(TOKEN_URL, data=data, headers={
        "Authorization": f"Basic {auth}",
        "Content-Type": "application/x-www-form-urlencoded",
    })
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode())


def run_local_auth(client_id: str, client_secret: str,
                   token_file: str = "~/spotify_tokens.json",
                   port: int = DEFAULT_PORT) -> Path:
    """Open the consent URL, catch the 127.0.0.1 callback, write tokens.

    Blocks until one request is handled. Returns the token file path.
    """
    import webbrowser

    caught: dict[str, str | None] = {}

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802 (http.server API)
            params = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            caught["code"] = params.get("code", [None])[0]
            caught["error"] = params.get("error", [None])[0]
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            done = "REMY: Spotify linked — you can close this tab." if caught.get("code") \
                else f"REMY: authorization failed ({caught.get('error')})."
            self.wfile.write(done.encode())

        def log_message(self, *args) -> None:  # silence the default stderr logging
            pass

    url = authorize_url(client_id, port)
    print("Authorize Spotify by opening:\n ", url)
    try:
        webbrowser.open(url)
    except Exception:
        pass

    server = HTTPServer((REDIRECT_HOST, port), Handler)
    try:
        server.handle_request()
    finally:
        server.server_close()

    if not caught.get("code"):
        raise RuntimeError(f"no authorization code received ({caught.get('error')})")

    result = exchange_code(client_id, client_secret, caught["code"], port)
    tokens = {
        "client_id": client_id,
        "client_secret": client_secret,
        "access_token": result["access_token"],
        "refresh_token": result["refresh_token"],
    }
    path = Path(token_file).expanduser()
    path.write_text(json.dumps(tokens, indent=2), encoding="utf-8")
    try:
        path.chmod(0o600)
    except OSError:
        pass
    return path
