"""SQLite job table (ADR 0002).

Single-writer: only REMY writes this table (the runner communicates through
event/heartbeat files, never IPC), so no locking dance is needed. A hand-rolled
~150-line table beats adopting a queue library because none of them store the
agent-session link a resumable job needs.
"""

from __future__ import annotations

import sqlite3
import time
import uuid
from pathlib import Path

from .model import TERMINAL, Job, JobState, can_transition

_COLUMNS = ("id", "prompt", "cwd", "state", "session_id", "unit_name",
            "created_ts", "heartbeat_ts", "updated_ts")


class JobStateError(Exception):
    pass


class JobStore:
    def __init__(self, db_path: str | Path) -> None:
        self.path = Path(db_path).expanduser()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.path))
        self._conn.row_factory = sqlite3.Row
        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS jobs ("
            " id TEXT PRIMARY KEY, prompt TEXT NOT NULL, cwd TEXT NOT NULL,"
            " state TEXT NOT NULL, session_id TEXT NOT NULL DEFAULT '',"
            " unit_name TEXT NOT NULL DEFAULT '', created_ts REAL NOT NULL,"
            " heartbeat_ts REAL NOT NULL DEFAULT 0, updated_ts REAL NOT NULL)")
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    # --- writes ---

    def create(self, prompt: str, cwd: str | Path, *,
               job_id: str | None = None, now: float | None = None) -> Job:
        now = time.time() if now is None else now
        job = Job(id=job_id or uuid.uuid4().hex[:12], prompt=prompt,
                  cwd=str(cwd), state=JobState.QUEUED,
                  created_ts=now, updated_ts=now)
        self._conn.execute(
            "INSERT INTO jobs (id, prompt, cwd, state, session_id, unit_name,"
            " created_ts, heartbeat_ts, updated_ts) VALUES (?,?,?,?,?,?,?,?,?)",
            (job.id, job.prompt, job.cwd, job.state, job.session_id,
             job.unit_name, job.created_ts, job.heartbeat_ts, job.updated_ts))
        self._conn.commit()
        return job

    def set_state(self, job_id: str, state: str, *, now: float | None = None) -> Job:
        job = self._require(job_id)
        if state != job.state and not can_transition(job.state, state):
            raise JobStateError(f"illegal transition {job.state} -> {state}")
        self._update(job_id, now, state=state)
        return self._require(job_id)

    def set_session(self, job_id: str, session_id: str, *,
                    now: float | None = None) -> None:
        self._update(job_id, now, session_id=session_id)

    def set_unit(self, job_id: str, unit_name: str, *,
                 now: float | None = None) -> None:
        self._update(job_id, now, unit_name=unit_name)

    def touch_heartbeat(self, job_id: str, ts: float) -> None:
        self._update(job_id, ts, heartbeat_ts=ts)

    # --- reads ---

    def get(self, job_id: str) -> Job | None:
        row = self._conn.execute(
            "SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
        return self._row_to_job(row) if row else None

    def all(self) -> list[Job]:
        rows = self._conn.execute(
            "SELECT * FROM jobs ORDER BY created_ts").fetchall()
        return [self._row_to_job(r) for r in rows]

    def active(self) -> list[Job]:
        return [j for j in self.all() if j.state not in TERMINAL]

    def by_state(self, state: str) -> list[Job]:
        return [j for j in self.all() if j.state == state]

    # --- internals ---

    def _require(self, job_id: str) -> Job:
        job = self.get(job_id)
        if job is None:
            raise JobStateError(f"no job {job_id}")
        return job

    def _update(self, job_id: str, now: float | None, **fields) -> None:
        fields["updated_ts"] = time.time() if now is None else now
        assignments = ", ".join(f"{col}=?" for col in fields)
        self._conn.execute(
            f"UPDATE jobs SET {assignments} WHERE id=?",
            (*fields.values(), job_id))
        self._conn.commit()

    @staticmethod
    def _row_to_job(row: sqlite3.Row) -> Job:
        return Job(**{col: row[col] for col in _COLUMNS})
