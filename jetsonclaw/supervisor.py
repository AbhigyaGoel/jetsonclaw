"""Boot guard + restart for self-iteration safety.

The contract that makes voice-driven self-modification safe to demo:
- every accepted change is a git commit, and the previous commit is recorded
  as last-known-good
- on startup we count boots; mark_healthy() resets the counter after the app
  survives its first minute
- if the app crash-loops (3 boots without ever reaching healthy), the next
  boot auto-reverts the repo to last-known-good before loading anything
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

HEALTHY_AFTER_SECS = 60.0
CRASH_LOOP_THRESHOLD = 3


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True, text=True, timeout=30,
    )
    if result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)}: {result.stderr.strip()}")
    return result.stdout.strip()


class BootGuard:
    def __init__(self, state_dir: str | Path, repo_dir: str | Path) -> None:
        self._state = Path(state_dir).expanduser()
        self._repo = Path(repo_dir).expanduser()
        self._counter_file = self._state / "boot_count"
        self._last_good_file = self._state / "last_good_ref"

    # --- boot counting ---

    def _read_count(self) -> int:
        try:
            return int(self._counter_file.read_text().strip())
        except (FileNotFoundError, ValueError):
            return 0

    def mark_boot(self) -> int:
        self._state.mkdir(parents=True, exist_ok=True)
        count = self._read_count() + 1
        self._counter_file.write_text(str(count))
        return count

    def mark_healthy(self) -> None:
        self._counter_file.write_text("0")

    def crash_looping(self) -> bool:
        return self._read_count() > CRASH_LOOP_THRESHOLD

    # --- known-good tracking ---

    def record_good(self, ref: str | None = None) -> None:
        if ref is None:
            ref = _git(self._repo, "rev-parse", "HEAD")
        self._state.mkdir(parents=True, exist_ok=True)
        self._last_good_file.write_text(ref)

    def last_good(self) -> str | None:
        try:
            return self._last_good_file.read_text().strip() or None
        except FileNotFoundError:
            return None

    def revert_to_last_good(self) -> str | None:
        """Hard-reset the repo to the recorded good commit. Returns the ref."""
        ref = self.last_good()
        if ref is None:
            return None
        _git(self._repo, "reset", "--hard", ref)
        self.mark_healthy()
        return ref


def restart_in_place() -> None:
    """Re-exec the current process — works under systemd and bare terminals."""
    os.execv(sys.executable, [sys.executable, "-m", "jetsonclaw", *sys.argv[1:]])
