# OpenVoiceOS/ovos-core — PORT

Community-maintained Mycroft successor. A bus-based intent pipeline where each
utterance flows through an ordered list of confidence-tiered matchers until one
claims it.

- **Stars/health:** 283, active (2026-08) · **License:** Apache-2.0 (portable
  with NOTICE)

## Does better than REMY
REMY routes essentially everything to the Claude Code brain. OVOS runs a
deterministic, ordered, confidence-tiered pipeline (`stop_high` → `converse` →
high-conf intents → medium → `common_qa` → fallback) so cheap exact matches
short-circuit before expensive stages. This is the local intent router REMY
lacks — it would resolve "stop"/"pause"/skill-owned phrases locally without ever
waking (and billing) Claude Code.

## Read these files
- `OpenVoiceOS/ovos-core@91021e7:docs/pipeline.md:L1-60` — the ordered-matcher
  pipeline with `_high/_medium/_low` suffixes selecting `match_high/medium/low`
  on a `ConfidenceMatcherPipeline`, per-`Session` reconfigurable. The best design
  doc for a tiered local-vs-agent router.
- `ovos_core/intent_services/dispatcher.py:L1-80` — `IntentDispatcher` emits
  `handler.start` then exactly one terminal (`complete`/`error`/timeout) per
  dispatch, with a `DEFAULT_HANDLER_TIMEOUT = 5*60` per in-flight handler.

## Lift
The confidence-tier ordering, and the single-terminal + per-handler timeout
dispatch contract (guarantees REMY's EventBus doesn't clearly have today).

## Avoid
The full `MessageBusClient` / `mycroft.conf` / entry-point plugin machinery —
heavy websocket-bus infrastructure; REMY's async EventBus is lighter.

## License constraint
Apache-2.0 — portable with attribution.

## Effort
**M** — port the pattern, not the code.
