# ADR 0002: Detached jobs as systemd-run user units over a sqlite job table

Status: proposed
Date: 2026-08-06

## Context

REMY runs one utterance at a time. `_route_lock` (`app.py:53`) is held for the
whole of `_route` (`app.py:196-199`), and the background loop refuses to run
while it is held (`app.py:103-104`). Agent work happens inside that lock, so
nothing - not chat, not a watcher - proceeds while an agent runs. Agent
sessions are subprocesses whose only persistence is `--continue`, and nothing
survives REMY restarting itself, which self-modification does routinely
(`selfiterate.py:162`, `supervisor.py:84-86`).

Demo 4 ("get my CS104 repo, work the assignment, tell me when it's done")
requires a 30-plus-minute job that runs while the owner keeps talking, reports
progress on request, cancels by voice, survives a REMY restart, and announces
completion. Multiple such jobs may coexist.

Correction to the program brief: the 600s figure (`config.py:84`) is applied
per stdout line read, so it is an inactivity timeout, not a wall-clock cap - a
working session already runs for hours. The true ceiling is the lock plus the
lack of persistence, not a 10-minute wall.

Research (`docs/research/deep-dives/`: openhands-software-agent-sdk,
litements-litequeue, peter-wangxu-persist-queue, coleifer-huey) found no
job-queue library worth a dependency: huey deletes the row before running the
task (no crash recovery), APScheduler persists schedules not running-job state,
arq/rq need redis. The needed shape is jobs-as-rows with an agent-session link,
a pause state, and a crash lease - which no library provides and a ~150-line
sqlite table does.

## Decision

A detached job is a `systemd-run --user` transient unit that runs a small
SDK-based runner process. REMY owns a sqlite job table and reads per-job files;
it never holds an IPC channel to the runner.

- Job row: `{id, session_id, unit_name, cwd, state, prompt, created_ts,
  heartbeat_ts}`. State machine: `queued -> running -> {done, failed,
  cancelled}`, with `paused` reachable from `running`.
- Launch: `systemd-run --user --unit=remy-job-<id> --collect
  -p RuntimeMaxSec=<wall> -p MemoryMax=<cap> python3 -m remy.jobrunner <id>`.
  The unit is a child of the user manager, not of REMY, so it outlives REMY's
  self-restart. Requires `loginctl enable-linger` once (a doctor check).
- Progress: the runner appends `~/.remy/jobs/<id>/events.jsonl` (OpenHands
  pattern) and touches `~/.remy/jobs/<id>/heartbeat`. "How's it going?" tails
  the events file; completion is the runner's final event seen by a watcher.
- Cancel: `systemctl --user stop remy-job-<id>` (SIGTERM then SIGKILL).
- Crash recovery: on boot, for each row in `running`, check the unit's
  `ActiveState`; only if the unit is gone do we reconcile the row (to `failed`
  or `queued`). This is persist-queue's boot sweep made pid/unit-gated, never
  the unconditional flip that would double-run a live job.
- The runner uses the Agent SDK (ADR 0001) with `resume=<session_id>` so a
  job re-attaches to its exact Claude session after any restart.

The lock is then only ever what its name says: one utterance through routing at
a time. Chat and quick skills stay in REMY's process; long agent work is out.

## Rationale

- systemd-run gives detachment, wall-clock kill (`RuntimeMaxSec`), journald
  logs, and cancellation for free, and REMY wants transient units for
  sandboxing anyway (ADR 0003) - one mechanism serves both.
- Files-not-IPC means REMY can crash and restart without losing the ability to
  observe or reconcile a job. The recovery state is one row.
- A hand-rolled sqlite table is smaller than adopting-then-fighting any queue
  library and is the only option that stores the agent-session link.

## Alternatives rejected

- In-process `asyncio.Task` per job. Rejected: dies with REMY's frequent
  self-restart; the whole point is surviving it.
- A queue library (huey/arq/rq/APScheduler). Rejected for the specific reasons
  above; all lack the agent-session link.
- A long-lived worker daemon REMY talks to over a socket. Rejected: adds a
  second always-on process and an IPC protocol to a box that restarts itself;
  files are simpler and restart-proof.

## Consequences

- New runtime dependency on user-session systemd with lingering enabled;
  `--doctor` must check `loginctl show-user` for linger and `systemctl --user`
  availability.
- A new `remy/jobrunner.py` entrypoint and a `remy/jobs/` store module.
- The web dashboard and TUI gain a jobs view fed by the same event files.
- Disk: runaway jobs need a watchdog that `du -s` the job dir and a stale-
  heartbeat kill; systemd has no per-directory quota.

## Verify on-box

- `systemd-run --user` transient unit survives `systemctl --user restart` of
  REMY and a full re-exec.
- `RuntimeMaxSec` and `MemoryMax` are honored in `--user` mode on systemd 249
  (memory/pids delegate by default; CPU may not - see ADR 0003).
- Reconciliation correctly distinguishes a live unit from a dead one after an
  unclean REMY exit.
