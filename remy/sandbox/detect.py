"""Can the sandbox actually run on this host? (ADR 0003)

The whole bwrap plan hinges on unprivileged user namespaces being enabled on the
L4T r36 kernel — the biggest on-box unknown in the program. These checks answer
it from --doctor. Everything returns False (never raises) off-Linux or when a
tool is missing, so calling them on the dev box is safe.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


def bwrap_available() -> bool:
    return shutil.which("bwrap") is not None


def userns_available() -> bool:
    """Can this user create an unprivileged user namespace? bwrap needs it, and
    jammy's package is non-setuid, so there is no fallback if this is off."""
    if shutil.which("unshare") is None:
        return False
    try:
        result = subprocess.run(
            ["unshare", "--user", "--map-root-user", "true"],
            capture_output=True, timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return result.returncode == 0


def cgroup_v2_delegation() -> bool:
    """cgroup v2 with a delegated memory controller, needed for MemoryMax in
    `systemd-run --user` scopes."""
    controllers = Path("/sys/fs/cgroup/cgroup.controllers")
    try:
        return controllers.is_file() and "memory" in controllers.read_text()
    except OSError:
        return False


def sandbox_report() -> dict[str, bool]:
    """Everything --doctor needs, in one call."""
    return {
        "bwrap": bwrap_available(),
        "userns": userns_available(),
        "cgroup_v2": cgroup_v2_delegation(),
    }
