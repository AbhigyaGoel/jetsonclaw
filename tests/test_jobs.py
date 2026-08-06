import pytest

from remy.jobs import JobStateError, JobStore, can_transition, reconcile
from remy.jobs.model import ACTIVE, TERMINAL, Job, JobState

NOW = 1_000_000.0


def store(tmp_path) -> JobStore:
    return JobStore(tmp_path / "jobs.db")


# --- state machine ----------------------------------------------------------

def test_legal_transitions():
    assert can_transition(JobState.QUEUED, JobState.RUNNING)
    assert can_transition(JobState.RUNNING, JobState.DONE)
    assert can_transition(JobState.RUNNING, JobState.PAUSED)
    assert can_transition(JobState.PAUSED, JobState.RUNNING)


def test_illegal_transitions():
    assert not can_transition(JobState.QUEUED, JobState.DONE)
    assert not can_transition(JobState.DONE, JobState.RUNNING)
    assert not can_transition(JobState.CANCELLED, JobState.RUNNING)


def test_state_sets_are_disjoint_and_cover():
    assert ACTIVE.isdisjoint(TERMINAL)
    assert Job("i", "p", "/w").state == JobState.QUEUED


# --- store ------------------------------------------------------------------

def test_create_starts_queued(tmp_path):
    job = store(tmp_path).create("do a thing", "/work", now=NOW)
    assert job.state == JobState.QUEUED
    assert job.id and job.created_ts == NOW


def test_roundtrip_persists_across_reopen(tmp_path):
    s = store(tmp_path)
    s.create("task", "/w", job_id="abc", now=NOW)
    s.set_session("abc", "sess-1", now=NOW)
    s.set_unit("abc", "remy-job-abc", now=NOW)
    s.close()

    reopened = JobStore(tmp_path / "jobs.db")
    got = reopened.get("abc")
    assert got.prompt == "task"
    assert got.session_id == "sess-1"
    assert got.unit_name == "remy-job-abc"


def test_set_state_enforces_machine(tmp_path):
    s = store(tmp_path)
    s.create("t", "/w", job_id="j", now=NOW)
    s.set_state("j", JobState.RUNNING, now=NOW)
    assert s.get("j").state == JobState.RUNNING
    with pytest.raises(JobStateError):
        s.set_state("j", JobState.QUEUED, now=NOW)  # no way back to queued


def test_set_state_unknown_job_raises(tmp_path):
    with pytest.raises(JobStateError):
        store(tmp_path).set_state("nope", JobState.RUNNING)


def test_active_excludes_terminal(tmp_path):
    s = store(tmp_path)
    s.create("a", "/w", job_id="a", now=NOW)
    s.create("b", "/w", job_id="b", now=NOW)
    s.set_state("b", JobState.RUNNING, now=NOW)
    s.set_state("b", JobState.DONE, now=NOW)
    active_ids = {j.id for j in s.active()}
    assert active_ids == {"a"}


def test_touch_heartbeat(tmp_path):
    s = store(tmp_path)
    s.create("t", "/w", job_id="j", now=NOW)
    s.touch_heartbeat("j", NOW + 5)
    assert s.get("j").heartbeat_ts == NOW + 5


# --- reconciliation ---------------------------------------------------------

def test_reconcile_fails_only_dead_units(tmp_path):
    s = store(tmp_path)
    for jid in ("live", "dead", "queued"):
        s.create("t", "/w", job_id=jid, now=NOW)
    s.set_state("live", JobState.RUNNING, now=NOW)
    s.set_unit("live", "remy-job-live", now=NOW)
    s.set_state("dead", JobState.RUNNING, now=NOW)
    s.set_unit("dead", "remy-job-dead", now=NOW)

    alive = {"remy-job-live"}
    flipped = reconcile(s, lambda unit: unit in alive, now=NOW)

    assert flipped == ["dead"]
    assert s.get("live").state == JobState.RUNNING   # untouched
    assert s.get("dead").state == JobState.FAILED
    assert s.get("queued").state == JobState.QUEUED  # never was running


def test_reconcile_is_idempotent(tmp_path):
    s = store(tmp_path)
    s.create("t", "/w", job_id="d", now=NOW)
    s.set_state("d", JobState.RUNNING, now=NOW)
    reconcile(s, lambda unit: False, now=NOW)
    # second sweep sees a terminal job and does nothing
    assert reconcile(s, lambda unit: False, now=NOW) == []
