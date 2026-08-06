"""Detached-job model and state machine (ADR 0002).

A job is one long agent task that runs as a systemd-run --user unit outside
REMY's process, so it survives REMY restarting itself. REMY owns this row; the
runner writes event/heartbeat files. The row carries the agent session id so the
job re-attaches to its exact Claude session (resume=) after any restart.
"""

from __future__ import annotations

from dataclasses import dataclass


class JobState:
    QUEUED = "queued"
    RUNNING = "running"
    PAUSED = "paused"
    DONE = "done"
    FAILED = "failed"
    CANCELLED = "cancelled"


# Nothing transitions out of a terminal state.
TERMINAL = frozenset({JobState.DONE, JobState.FAILED, JobState.CANCELLED})
ACTIVE = frozenset({JobState.QUEUED, JobState.RUNNING, JobState.PAUSED})

_TRANSITIONS: dict[str, frozenset[str]] = {
    JobState.QUEUED: frozenset({JobState.RUNNING, JobState.CANCELLED}),
    # a running unit that vanishes reconciles to failed; the owner can cancel
    JobState.RUNNING: frozenset({JobState.PAUSED, JobState.DONE,
                                 JobState.FAILED, JobState.CANCELLED}),
    # paused unit gone == crashed -> failed; may resume or be cancelled
    JobState.PAUSED: frozenset({JobState.RUNNING, JobState.CANCELLED,
                                JobState.FAILED}),
    JobState.DONE: frozenset(),
    JobState.FAILED: frozenset(),
    JobState.CANCELLED: frozenset(),
}


def can_transition(frm: str, to: str) -> bool:
    return to in _TRANSITIONS.get(frm, frozenset())


@dataclass(frozen=True)
class Job:
    id: str
    prompt: str
    cwd: str
    state: str = JobState.QUEUED
    session_id: str = ""   # Claude session, for resume= after a restart
    unit_name: str = ""    # systemd --user transient unit
    created_ts: float = 0.0
    heartbeat_ts: float = 0.0
    updated_ts: float = 0.0

    @property
    def terminal(self) -> bool:
        return self.state in TERMINAL
