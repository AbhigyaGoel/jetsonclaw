# devgianlu/go-librespot — DEPEND (Spotify sidecar)

A Go Spotify Connect client, single portable binary (README targets Raspberry
Pi / embedded, so arm64 is fine), with a built-in **REST API + WebSocket
`/events`**.

- **Stars/health:** 345, very active (2026-08) · **License:** GPL-3.0
  (process-boundary only — never link into REMY's MIT code)

## Does better than REMY (the key Spotify win)
Play/pause/skip/now-playing **without the official Web API** and **without
registering a Premium developer app**. Three login flows: Zeroconf/Spotify
Connect discovery, interactive OAuth, or a raw access token. REMY's skill can
drop the OAuth-app registration and just POST to the local daemon; the WS
`/events` stream (`metadata`, `playing`, `paused`, `volume`, `album_cover_url`)
feeds REMY's dashboard "what's playing" for free.

Caveat: Spotify **Premium is still required** by Spotify's servers — but the app
registration / Web-API-token dance is eliminated.

## Read these files
- `devgianlu/go-librespot@48dd7c1:API.md` — the WS event schema (near 1:1 with
  REMY's dashboard state).
- `config_schema.json` — auth/backends config.
- `README.md` — login flows, ALSA backend (matches REMY's arecord/ALSA world).

## Lift
Run as a sidecar, drive via `http://localhost:<port>` + subscribe to `/events`.

## Avoid
Linking its GPL Go code into REMY — keep it a separate process so REMY stays MIT.

## License constraint
GPL-3.0 — separate-process aggregation only.

## Jetson cost
One Go binary (~15MB, arm64); ALSA already present. No model, no GPU.

## Effort
**S-M.**
