# peter-wangxu/persist-queue — PATTERN-ONLY

SQLite/file-backed queues with an ack variant (`SQLiteAckQueue`) whose whole
point is the property huey lacks: a gotten-but-unacked item stays in the DB as
`unack`, and on restart `resume_unack_tasks()` flips every `unack` row back to
`ready`. That is REMY's crash-recovery semantic in library form. Still not
worth depending on: sync API, thread-lock based, no job metadata or state
machine beyond ack states, and maintenance is slow (last push 2026-01).

- **Stars/health:** 390, slow (2026-01) · **License:** BSD-3-Clause

## Does better than REMY
Demonstrates ack-state crash recovery: five states and a restart sweep, in
~380 lines of sqlite3.

## Read these files
- `peter-wangxu/persist-queue@b4fb6d1:persistqueue/sqlackqueue.py:L18-23` — `AckStatus`: inited/ready/unack/acked/ack_failed
- `@b4fb6d1:persistqueue/sqlackqueue.py:L72-80` — `resume_unack_tasks()`: one UPDATE unack->ready at open; contrast with litequeue's time-threshold `retry_expired` (better, since REMY's job may legitimately still be running in a detached unit)

## Lift
The restart sweep concept, but gated: on REMY boot, for each `running` job row
check whether its systemd unit / pid is actually alive before flipping to
`queued` (persist-queue flips unconditionally because its workers die with the
process; REMY's detached jobs do not).

## Avoid
Depending on it; unconditional resume would double-run a job that survived
REMY's restart inside its own systemd unit.

## License constraint
BSD-3-Clause, compatible, moot given verdict.

## Effort
S (pattern only)
