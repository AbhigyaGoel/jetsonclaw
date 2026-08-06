# litements/litequeue — PATTERN-ONLY

Single-module SQLite message queue (~970 lines, zero deps). One table, WAL
mode, four states (READY/LOCKED/DONE/FAILED), optimistic claim via a
`claim_id` compare-and-swap, and `retry_expired()` to reclaim stale LOCKED
rows, which is exactly the watchdog-reclaim REMY's job table needs after a
crash. Too small to depend on for job semantics (no pause, no progress
fields, no job metadata), but the schema and the stale-claim idiom are the
model for REMY's ~150-line job store.

- **Stars/health:** 231, active (2026-07) · **License:** MIT

## Does better than REMY
REMY has no durable queue at all. litequeue shows the minimal correct shape:
status ints + WAL + CAS claims + time-based lock expiry, all in stdlib sqlite3.

## Read these files
- `litements/litequeue@9e286af:src/litequeue/__init__.py:L102-106` — `MessageStatus`: READY=0, LOCKED=1, DONE=2, FAILED=3
- `@9e286af:src/litequeue/__init__.py:L388-393` — WAL pragma on open (idempotent check first)
- `@9e286af:src/litequeue/__init__.py:L555-612` — `pop()`: single UPDATE...RETURNING claim with `claim_id`, no SELECT-then-UPDATE race
- `@9e286af:src/litequeue/__init__.py:L668-713` — `done()`/`mark_failed()` gated on `claim_id` AND status=LOCKED (a stale worker cannot complete a reclaimed job)
- `@9e286af:src/litequeue/__init__.py:L796-812` — `retry_expired(threshold_seconds)`: LOCKED rows older than threshold flip back to READY; this is crash recovery

## Lift
The schema shape and three idioms into REMY's own job table: (1) status as a
small int state machine, extended with paused/cancelled; (2) claim_id CAS so a
resurrected old worker can't stomp a reclaimed job; (3) retry_expired as the
watchdog's crash-recovery sweep, driven off a heartbeat timestamp column.

## Avoid
Depending on it: messages are opaque blobs, REMY jobs need columns
(session_id, cwd, transcript path, progress text, announced flag) and
extra states. Sync API only; fine because REMY would call it from a single
asyncio task anyway, but hand-rolling with the same pragmas costs less than
adapting.

## License constraint
MIT, could vendor the single file, but PATTERN-ONLY is less code.

## Effort
S (read it once, write REMY's table with the same idioms)
