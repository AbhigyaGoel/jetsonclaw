"""Detached job engine core (ADR 0002): the sqlite job table, state machine, and
crash-recovery sweep. The runner (jobrunner.py) and systemd-run launch wire onto
this and land with the on-box gate (docs/design/on-box-checklist.md)."""

from .model import ACTIVE, TERMINAL, Job, JobState, can_transition
from .reconcile import reconcile
from .store import JobStateError, JobStore

__all__ = [
    "ACTIVE", "TERMINAL", "Job", "JobState", "can_transition",
    "reconcile", "JobStore", "JobStateError",
]
