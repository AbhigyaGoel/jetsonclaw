"""Env-scrub before spawning an agent session (ADR 0004).

Provider secrets must not ride into the agent's environment, where a synthesized
skill or the agent itself could echo them into a transcript. Strip them from the
child env; keep everything the CLI needs (PATH, HOME, and — critically —
CLAUDE_CODE_OAUTH_TOKEN, the subscription auth).

ANTHROPIC_API_KEY is scrubbed too: even if it leaked into REMY's env, the agent
must fall back to subscription billing, never pay-as-you-go (see CLAUDE.md).
"""

from __future__ import annotations

from collections.abc import Mapping

# Exact names to drop.
_DENY_EXACT = frozenset({
    "ANTHROPIC_API_KEY",
    "OPENAI_API_KEY",
    "GROQ_API_KEY",
    "GH_TOKEN",
    "GITHUB_TOKEN",
})
# Prefixes to drop (any var starting with one of these). REMY_CRED_* are broker
# bearers — the agent must never inherit a live one.
_DENY_PREFIX = ("SPOTIFY_", "REMY_CRED_")


def scrub_env(env: Mapping[str, str]) -> dict[str, str]:
    """Return a copy of env with provider secrets removed. Matching is
    case-insensitive so a mixed-case variant can't slip a secret through."""
    return {
        key: value
        for key, value in env.items()
        if key.upper() not in _DENY_EXACT and not key.upper().startswith(_DENY_PREFIX)
    }
