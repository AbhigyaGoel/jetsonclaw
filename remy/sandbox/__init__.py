"""Sandbox foundation (ADR 0003): bubblewrap profiles + on-box viability checks.

This package only BUILDS sandbox command lines and DETECTS whether the host can
run them. Wiring skill execution through it is gated on the on-box userns check
(docs/design/on-box-checklist.md) — the single biggest unknown in the program.
"""
