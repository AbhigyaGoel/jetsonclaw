"""Tiny language helpers for spoken output."""

from __future__ import annotations

from typing import Sequence


def natural_list(items: Sequence[str], limit: int = 3) -> str:
    """Join items the way a person says them: 'A, B, and C'."""

    items = list(items)[:limit]
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f"{items[0]} and {items[1]}"
    return f"{', '.join(items[:-1])}, and {items[-1]}"
