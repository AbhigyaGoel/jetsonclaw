"""Redact secret-shaped tokens before text is written to durable stores.

REMY logs everything it says and hears (episodic memory, the evolution journal,
daily summaries). A credential that lands in one of those files leaks forever and
can be read back into a prompt. This filter strips the handful of unambiguous
secret shapes on the way to disk.

Deliberately NARROW: each pattern matches a specific, high-entropy credential
format with a fixed prefix. It must never eat ordinary speech — the cost of a
false positive is hidden real output, so we do not chase generic "long random
string" heuristics. Add a pattern only when you can name the exact token it
matches.
"""

from __future__ import annotations

import re

# (kind, pattern). Each pattern captures the whole secret; the Bearer/JSON ones
# use a group so the surrounding label survives.
_SECRETS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("github-token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b")),
    ("google-oauth", re.compile(r"\bya29\.[A-Za-z0-9._-]{20,}")),
    ("google-api-key", re.compile(r"\bAIza[A-Za-z0-9_-]{20,}\b")),
    ("openai-anthropic-key", re.compile(r"\bsk-(?:ant-)?[A-Za-z0-9_-]{20,}\b")),
    ("slack-token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b")),
    ("aws-access-key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("stripe-key", re.compile(r"\b[rs]k_(?:live|test)_[A-Za-z0-9]{16,}\b")),
)

# "Authorization: Bearer <token>" — keep the scheme, drop the token.
_BEARER = re.compile(r"\b(Bearer\s+)[A-Za-z0-9._~+/=-]{20,}")

# JSON-ish credential fields: "access_token": "…" — keep the key, drop the value.
_JSON_SECRET = re.compile(
    r'("(?:access|refresh|id)_token"\s*:\s*")[^"]{6,}(")'
    r'|("client_secret"\s*:\s*")[^"]{6,}(")')


def redact(text: str) -> str:
    """Return text with known credential shapes replaced by a labelled marker."""
    if not text:
        return text
    out = text
    for kind, pattern in _SECRETS:
        out = pattern.sub(f"[redacted:{kind}]", out)
    out = _BEARER.sub(r"\1[redacted:bearer]", out)
    out = _JSON_SECRET.sub(_json_repl, out)
    return out


def _json_repl(m: re.Match[str]) -> str:
    # Only one of the two alternations matches per call.
    if m.group(1) is not None:
        return f"{m.group(1)}[redacted]{m.group(2)}"
    return f"{m.group(3)}[redacted]{m.group(4)}"
