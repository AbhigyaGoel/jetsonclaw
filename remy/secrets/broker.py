"""Token broker (ADR 0004), aws-vault's credential-server shape.

A skill that needs a provider credential is granted a per-invocation bearer and a
loopback URL; it fetches a fresh ~1-hour access token on demand. The refresh
token and the encryption key never leave the broker, so a fully compromised skill
still only holds a short-lived access token and a stale-on-next-run bearer.

TokenProviders are injected: a real one reads the refresh token from the store
and calls the provider's token endpoint (on-box); tests inject a static one. The
HTTP layer is thin — `_handle` carries the auth logic and is tested directly.
"""

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from secrets import token_urlsafe
from typing import Protocol


class TokenProvider(Protocol):
    name: str
    def access_token(self) -> tuple[str, float]: ...  # (token, expires_at)


class TokenBroker:
    def __init__(self, host: str = "127.0.0.1") -> None:
        self._host = host
        self._providers: dict[str, TokenProvider] = {}
        self._grants: dict[str, str] = {}  # bearer -> provider name
        # grant/revoke run on REMY's thread; _handle runs on the HTTP thread.
        self._lock = threading.Lock()
        self._server: HTTPServer | None = None
        self._thread: threading.Thread | None = None

    def register(self, provider: TokenProvider) -> None:
        self._providers[provider.name] = provider

    def grant(self, provider: str) -> dict[str, str]:
        """Mint a fresh bearer for a skill spawn; return the env to inject."""
        if provider not in self._providers:
            raise KeyError(f"no credential provider {provider!r}")
        bearer = token_urlsafe(24)
        with self._lock:
            self._grants[bearer] = provider
        return {
            "REMY_CRED_URL": self.url,
            "REMY_CRED_TOKEN": bearer,
            "REMY_CRED_PROVIDER": provider,
        }

    def revoke(self, bearer: str) -> None:
        with self._lock:
            self._grants.pop(bearer, None)

    def _handle(self, path: str, bearer: str) -> tuple[int, dict]:
        """Auth + dispatch. path is /token/<provider>. Pure — no I/O.

        Bearer travels over plaintext loopback (127.0.0.1 only); the design
        accepts that per ADR 0004, leaning on per-invocation bearers and
        short-lived access tokens rather than TLS on localhost."""
        with self._lock:
            provider = self._grants.get(bearer)
        if provider is None:
            return 403, {"error": "invalid or revoked bearer"}
        wanted = path.rsplit("/", 1)[-1]
        if wanted != provider:
            return 403, {"error": "bearer not granted for this provider"}
        token, expires_at = self._providers[provider].access_token()
        return 200, {"access_token": token, "expires_at": expires_at}

    # --- live loopback server (used at runtime; also covered by one test) ---

    @property
    def url(self) -> str:
        port = self._server.server_address[1] if self._server else 0
        return f"http://{self._host}:{port}"

    def start(self) -> None:
        broker = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self) -> None:  # noqa: N802 (http.server API)
                auth = self.headers.get("Authorization", "")
                bearer = auth[7:] if auth.startswith("Bearer ") else ""
                status, body = broker._handle(self.path, bearer)
                payload = json.dumps(body).encode()
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)

            def log_message(self, *args) -> None:
                pass

        self._server = HTTPServer((self._host, 0), Handler)
        self._thread = threading.Thread(target=self._server.serve_forever,
                                        daemon=True)
        self._thread.start()

    def stop(self) -> None:
        if self._server is not None:
            self._server.shutdown()
            self._server.server_close()
            self._server = None
