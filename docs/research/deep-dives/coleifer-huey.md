# coleifer/huey — IGNORE

Mature task queue (Redis/SQLite/file/in-memory backends) with a separate
consumer process running worker threads. The SQLite backend looks like REMY's
answer on paper, but two disqualifiers: `dequeue()` DELETES the task row as it
hands it to a worker, so a crash mid-task loses the job (no ack/lease, no
requeue-on-crash), and there is no asyncio worker, only an `aget_result()`
polling helper for callers. It solves "run this function later", not REMY's
"long-lived agent session with progress, cancel, and crash resume".

- **Stars/health:** 6.0k, active (2026-08) · **License:** MIT

## Does better than REMY
Nothing REMY needs: its durability covers queued-but-not-started tasks only.
REMY's critical window is DURING the 30-minute agent run, where huey holds the
task solely in worker memory.

## Read these files
- `coleifer/huey@5391156:huey/storage.py:L818-843` — SqliteStorage DDL: kv, schedule, task, counter tables, WAL default
- `@5391156:huey/storage.py:L885-896` — `dequeue()` = SELECT then DELETE; row is gone before the task runs, this is the disqualifier
- `@5391156:huey/contrib/asyncio.py:L1-40` — `aget_result()` is just backoff polling; the consumer itself is threads, not asyncio

## Lift
Nothing beyond confirmation that a queue-of-functions abstraction is the wrong
shape; REMY jobs are rows with a lifecycle, not serialized callables.

## Avoid
Adopting it and rebuilding ack/lease semantics on top; running a second
consumer process just to execute one concurrent job on an 8GB board.

## License constraint
MIT, irrelevant given verdict.

## Effort
n/a
