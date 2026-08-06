# pytest-dev/pluggy — PORT

The hook framework under pytest/tox/devpi. `@hookspec` defines contracts,
`@hookimpl` implements, `PluginManager` registers + dispatches.

- **Stars/health:** 1.7k, active (2026-08) · **License:** MIT (vendorable)

## Does better than REMY
Turns REMY's implicit "handler.py exposes `handle`/`selftest`/`converse`"
convention into an explicit, validated contract with ordering control — cleaner
than string-matching method names.

## Read these files
- `pytest-dev/pluggy@f632a4d:src/pluggy/_hooks.py:L44-75` — hookimpl options:
  `firstresult` (stop at first non-None — ideal for REMY "first skill that claims
  the utterance wins"), `tryfirst`/`trylast` (priority ordering for trigger
  overlap), `optionalhook`, `wrapper`.
- `src/pluggy/_manager.py:L380-405` — `load_setuptools_entrypoints()` with
  `is_blocked()`: a ready-made **quarantine** primitive — mark a failing skill
  blocked instead of the rename-to-`.failed` dance; it stays registered-but-inert
  with a clear `unblock` recovery path.

## Lift
The hookspec-with-`firstresult` + ordering model, and the `is_blocked` quarantine
registry as an in-memory layer over the file-based `.failed` rename.

## Avoid
Full setuptools entry-point discovery — REMY skills are dirs, not installed
dists; keep filesystem discovery but validate against a hookspec-style contract.

## License constraint
MIT — vendorable with attribution.

## Effort
**M.**
