# OpenHands/software-agent-sdk — PATTERN-ONLY

The rewritten OpenHands agent core (the old All-Hands-AI/OpenHands Python
internals moved here; the main repo is now a TS app). Its conversation layer is
the best public reference for long-running-agent durability: an append-only
file-per-event log (`events/event-00001-<uuid>.json`) plus `base_state.json`,
resume by replay, a TTL'd owner-lease file with pid-liveness for crash
takeover, and a thread-safe cooperative CancellationToken checked by in-flight
tools. LLM-agnostic stack (litellm), so REMY takes patterns, not code paths.

- **Stars/health:** 961 (parent OpenHands app repo 83k), active (2026-08) · **License:** MIT

## Does better than REMY
REMY persists nothing about an agent run. OpenHands persists everything as
individually-fsyncable event files, so any observer (their "how's it going"
equivalent) reads progress without touching the running process, and a crashed
conversation resumes from the log.

## Read these files
- `OpenHands/software-agent-sdk@b35c2fe:openhands-sdk/openhands/sdk/conversation/persistence_const.py:L1-11` — layout: `base_state.json` + `events/event-{idx:05d}-{event_id}.json`
- `@b35c2fe:openhands-sdk/openhands/sdk/conversation/event_store.py:L30-58` — `EventLog`: FileStore-backed, lock file, index rebuilt by directory scan on open (crash-safe by construction)
- `@b35c2fe:openhands-sdk/openhands/sdk/conversation/cancellation.py:L1-43` — `CancellationToken`: threading.Event, deliberately not asyncio, so tool threads and the loop share it
- `@b35c2fe:openhands-agent-server/openhands/agent_server/conversation_lease.py:L18-50` — `owner_lease.json`: owner id, generation, expires_at (45s TTL), owner_pid; takeover checks pid liveness

## Lift
Three patterns for REMY jobs: (1) per-job dir `~/.remy/jobs/<id>/` with
`state.json` + append-only `events.jsonl`; REMY answers "how's it going" by
reading the tail, even for a job running in a detached systemd unit; (2)
lease/heartbeat file with pid + expiry as the job-runner liveness signal the
watchdog and boot-recovery sweep consult; (3) cancellation as a cooperative
flag (for REMY: a `cancel` sentinel file the runner polls between SDK
messages, since SIGTERM mid-tool-call is handled by the CLI anyway).

## Avoid
Adopting the SDK itself: litellm-based agent loop duplicates what Claude Code
already does, and REMY's transcript persistence comes free from the CLI's own
session JSONL. File-per-event (their choice) is overkill next to a single
JSONL; they need concurrent multi-writer safety, REMY does not.

## License constraint
MIT, patterns and code both fine; patterns suffice.

## Effort
S-M (the three patterns are each <50 lines in REMY)
