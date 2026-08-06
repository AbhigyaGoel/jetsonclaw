"""Credential-store viability checks for --doctor (ADR 0004).

Returns False (never raises) when a tool is missing or off-Linux, so calling on
the dev box is safe.
"""

from __future__ import annotations

import shutil
import stat
from pathlib import Path


def age_available(binary: str = "age") -> bool:
    return shutil.which(binary) is not None


def secrets_dir_secure(directory: str | Path) -> bool:
    """The store dir, if it exists, must be 0700 (owner-only). A missing dir is
    fine — it's created 0700 on first write."""
    return _mode_ok(directory, 0o700)


def identity_file_secure(path: str | Path) -> bool:
    """The age identity file, if it exists, must be 0600 — a 0644 identity lets
    any local process decrypt every credential and bypass the broker."""
    return _mode_ok(path, 0o600, require_file=True)


def _mode_ok(target: str | Path, want: int, *, require_file: bool = False) -> bool:
    path = Path(target).expanduser()
    exists = path.is_file() if require_file else path.is_dir()
    if not exists:
        return True  # absent is fine; it's created with the right mode
    try:
        return stat.S_IMODE(path.stat().st_mode) == want
    except OSError:
        return False
