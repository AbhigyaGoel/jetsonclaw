"""Crash-recovery boot sweep (ADR 0002).

After an unclean REMY exit, a row can say `running` for a job whose systemd unit
is actually gone. This flips only those to `failed`. The check is gated on the
unit being dead — flipping a row whose unit is still alive would let the boot
sweep double-run a live job, which is the exact bug persist-queue's unconditional
sweep has. `unit_active` is injected so this is testable without systemd.
"""

from __future__ import annotations

from collections.abc import Callable

from .model import JobState
from .store import JobStore


def reconcile(store: JobStore, unit_active: Callable[[str], bool], *,
              now: float | None = None) -> list[str]:
    """Reconcile crashed jobs. Returns the ids flipped to failed."""
    reconciled = []
    for job in store.all():
        if job.state not in (JobState.RUNNING, JobState.PAUSED):
            continue
        if job.unit_name and unit_active(job.unit_name):
            continue  # still alive under the user manager — never touch it
        store.set_state(job.id, JobState.FAILED, now=now)
        reconciled.append(job.id)
    return reconciled
