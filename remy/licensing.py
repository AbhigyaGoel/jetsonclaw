"""License guard: keep GPL code out of REMY's process.

REMY is MIT. GPL-licensed dependencies are allowed only across a process
boundary (e.g. the `piper` binary invoked as a subprocess), never imported into
this interpreter. The original MIT Piper (rhasspy/piper, pip `piper-tts` <= 1.2)
was archived in October 2025; active development moved to OHF-Voice/piper1-gpl,
published as `piper-tts` >= 1.3 under GPL-3.0. Importing that in-process would
make REMY a GPL derivative — so the selftest/doctor gate refuses to go green
while it is installed.
"""

from __future__ import annotations

from importlib import metadata


def _is_gpl_piper(version: str, license_text: str) -> bool:
    """Decide from a distribution's metadata whether it is the GPL Piper line."""
    text = (license_text or "").upper()
    if "GPL" in text or "GENERAL PUBLIC LICENSE" in text:
        return True
    # piper1-gpl ships as piper-tts >= 1.3; the MIT rhasspy line stopped at 1.2.x.
    try:
        major_minor = tuple(int(part) for part in version.split(".")[:2])
    except ValueError:
        return False
    return major_minor >= (1, 3)


def gpl_piper_installed() -> str | None:
    """Return a human-readable reason if a GPL Piper is importable, else None."""
    try:
        dist = metadata.metadata("piper-tts")
    except metadata.PackageNotFoundError:
        return None  # not installed at all — nothing to import, nothing to leak
    version = dist.get("Version", "")
    classifiers = " ".join(dist.get_all("Classifier") or [])
    license_text = f"{dist.get('License') or ''} {classifiers}"
    if _is_gpl_piper(version, license_text):
        return (f"piper-tts {version} is GPL-licensed and importable in-process; "
                "uninstall it and run the piper binary out-of-process (audio/tts.py)")
    return None
