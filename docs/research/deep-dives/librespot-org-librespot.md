# librespot-org/librespot — VENDOR (MIT alt)

The upstream MIT Rust Spotify library the whole librespot family derives from.
It's a library / `librespot` CLI player with **no built-in HTTP control API**.

- **Stars/health:** 6.9k, active (2026-07) · **License:** MIT (vendorable)

## Does better than REMY
Plays Spotify **without the official Web API** and without registering a Premium
developer app — REMY currently uses the Web API (OAuth app registration +
tokens). MIT-clean if REMY wants to embed rather than run a GPL sidecar.

## Read these files
- Repo README + `src/` player entry — confirms the Connect/Zeroconf + token
  login model. No HTTP API in-tree (that's what `devgianlu/go-librespot` adds on
  top — see its deep-dive).

## Lift
The MIT core if REMY must avoid a GPL dependency. But you'd have to build the
REST/WS control surface yourself, which `go-librespot` already did.

## Avoid
Reinventing the control API when go-librespot exists — only prefer librespot if
the MIT requirement forbids a GPL sidecar process.

## License constraint
MIT — vendorable with attribution. (Spotify Premium still required by Spotify's
servers, as with the whole family.)

## Jetson cost
Rust binary, arm64; small. No model, no GPU.

## Effort
**L** — must build the control surface. Prefer `go-librespot` (S-M) unless the
MIT constraint is hard.
