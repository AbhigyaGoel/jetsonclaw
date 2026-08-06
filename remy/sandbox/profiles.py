"""bubblewrap sandbox profiles (ADR 0003).

REMY runs untrusted code — synthesized skills, pip installs, toolchain jobs — and
each needs containment sized to its job. One mechanism (bubblewrap for isolation,
`systemd-run --user --scope` for resource caps), three frozen profiles.

This module only BUILDS the argv; the loader wires it in once the on-box
unprivileged-userns check passes. The isolation boundary is what exists inside
the tmpfs root, not the PATH: ~/.remy, the secrets store, and the repo are simply
never mounted, so contained code cannot see them.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path  # noqa: TC003 (used in runtime type hints)


@dataclass(frozen=True)
class Profile:
    name: str
    memory_max: str        # systemd MemoryMax, e.g. "512M"
    runtime_max_secs: int  # systemd RuntimeMaxSec (wall-clock kill)
    network: bool          # default; profile A skills may opt in per manifest


# Profile A — run one skill (Python or shell). Locked down, no network default.
SKILL = Profile("skill", "512M", 30, network=False)
# Profile B — pip install into a dedicated venv. Network on, larger caps.
PIP = Profile("pip", "1G", 600, network=True)
# Profile C — long toolchain job (git/pip/compilers/node). Largest caps.
TOOLCHAIN = Profile("toolchain", "3G", 3600, network=True)

# Read-only OS mounts every profile needs to run interpreters and tools. Bound
# with --ro-bind-try so a path absent on one host doesn't abort the sandbox.
_RO_SYSTEM = ("/usr", "/bin", "/sbin", "/lib", "/lib64",
              "/etc/alternatives", "/etc/ssl", "/etc/resolv.conf")


def bwrap_argv(profile: Profile, command: list[str], writable: str | Path,
               *, network: bool | None = None) -> list[str]:
    """The bwrap portion: tmpfs root, read-only system, one writable dir.

    `writable` is the only host path the contained code can write (the skill
    dir or job dir). `network` overrides the profile default (manifest opt-in).
    """
    net = profile.network if network is None else network
    argv = ["bwrap", "--unshare-all"]
    if net:
        argv.append("--share-net")
    argv += ["--tmpfs", "/", "--proc", "/proc", "--dev", "/dev"]
    for path in _RO_SYSTEM:
        argv += ["--ro-bind-try", path, path]
    # Keep the caller's path verbatim — these are Linux paths; normalizing
    # through Path on a non-Linux host would mangle the separators.
    work = str(writable)
    argv += ["--bind", work, work, "--chdir", work, "--"]
    argv += list(command)
    return argv


def sandboxed_argv(profile: Profile, command: list[str], writable: str | Path,
                   *, network: bool | None = None) -> list[str]:
    """Full argv: `systemd-run --user --scope` (resource caps) wrapping bwrap.

    bwrap isolates the filesystem/namespaces; systemd-run supplies the memory,
    task, and wall-clock caps bwrap cannot express.
    """
    return [
        "systemd-run", "--user", "--scope", "--quiet",
        "-p", f"MemoryMax={profile.memory_max}",
        "-p", f"RuntimeMaxSec={profile.runtime_max_secs}",
        "-p", "TasksMax=256",
        "--",
        *bwrap_argv(profile, command, writable, network=network),
    ]
