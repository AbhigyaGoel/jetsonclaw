#!/usr/bin/env python3
"""Link Spotify to REMY using a 127.0.0.1 loopback redirect.

Spotify rejects `localhost` / LAN-IP redirects since 2025 — this uses 127.0.0.1.

1. Create an app at https://developer.spotify.com/dashboard
2. Add this redirect URI to the app:  http://127.0.0.1:8888/callback
3. Run:
     python3 scripts/spotify_auth.py --client-id XXX --client-secret YYY
   (or set SPOTIFY_CLIENT_ID / SPOTIFY_CLIENT_SECRET in the environment)
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from remy.skills.spotify_auth import DEFAULT_PORT, redirect_uri, run_local_auth


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--client-id", default=os.environ.get("SPOTIFY_CLIENT_ID"))
    parser.add_argument("--client-secret", default=os.environ.get("SPOTIFY_CLIENT_SECRET"))
    parser.add_argument("--token-file", default="~/spotify_tokens.json")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    args = parser.parse_args()

    if not args.client_id or not args.client_secret:
        parser.error("set --client-id/--client-secret or SPOTIFY_CLIENT_ID/SECRET")

    print("Register this redirect URI in your Spotify app:", redirect_uri(args.port))
    path = run_local_auth(args.client_id, args.client_secret,
                          args.token_file, args.port)
    print("Tokens written to", path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
