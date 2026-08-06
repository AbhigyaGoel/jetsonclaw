"""Credential store + token broker (ADR 0004).

The primary adversary is REMY's own synthesized skills and agent sessions
leaking secrets into prompts, transcripts, logs, or git — not another local user.
So secrets live age-encrypted outside the repo, and skills get short-lived access
tokens through a loopback broker, never the refresh secret or the encryption key.

This package builds the store, broker, and env-scrub. Real OAuth refreshers, the
age on-box round-trip, and wiring the broker into skill spawning land with the
on-box gate (docs/design/on-box-checklist.md).
"""
