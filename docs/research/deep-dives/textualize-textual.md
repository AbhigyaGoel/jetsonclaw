# Textualize/textual — DEPEND (already in use; adopt `textual serve`)

The TUI framework REMY already uses for its on-device TUI.

- **Stars/health:** 36.9k, active (2026-07) · **License:** MIT

## Does better than REMY
`textual serve "python -m remy_tui"` serves the **same TUI app in a browser** —
collapsing REMY's *two* frontends (Textual TUI + a separate hand-rolled PWA at
:8484) toward **one codebase**. textual-web adds firewall-busting remote access
for the phone surface.

## Read these files
- `Textualize/textual@06dbeef:README.md` — the "Textual ❤️ Web" / `textual serve`
  section.

## Lift
Replace/augment the hand-rolled PWA with `textual serve` for the live-state +
transcript panes; keep a thin PWA only for the phone mic button + phone-side TTS
(browser MediaRecorder / Web Speech, which textual-web can't do).

## Avoid
Expecting textual-web to cover the phone mic/TTS — that stays a small custom PWA.

## License constraint
MIT.

## Jetson cost
`textual-serve` — pure Python, negligible.

## Effort
**M.**
