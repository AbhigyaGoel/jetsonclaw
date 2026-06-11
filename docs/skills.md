# Skills

A skill is a directory under `~/.jetsonclaw/skills/` containing a `SKILL.md`. Skills are rescanned on every utterance with an mtime cache, so new or edited skills take effect immediately. No restart, no redeploy.

## Format

```markdown
---
name: weather
description: current weather
triggers:
  - weather
  - is it raining
action:
  command: curl -s "wttr.in/?format=%C+%t"
requires:
  bins: [curl]
---
Free-form notes for humans and agents.
```

| Field | Meaning |
|---|---|
| `name` | identifier, also used in logs |
| `description` | one line, shown in skill catalogs |
| `triggers` | case-insensitive regexes matched against the utterance |
| `action.command` | shell snippet; the utterance is in `$JARVIS_TEXT`; stdout is spoken |
| `action.script` | a Python file in the same directory exposing `handle(text) -> str` |
| `requires.bins` | binaries that must exist or the skill is hidden |
| `requires.pip` | pip packages the harness installs on activation |

## Script skills

```python
# handler.py
def handle(text: str) -> str:
    return "Heads!"

def selftest() -> str:        # optional but recommended
    assert handle("flip") in ("Heads!", "Tails!")
    return "ok"
```

## Synthesis

Saying "give yourself a ..." or "integrate with ..." starts an agent session that writes the skill. For real API integrations the agent is instructed to read the actual API docs via web fetch, write a proper module, declare pip dependencies in frontmatter, and include a `selftest()` that makes one cheap real call.

## Activation and quarantine

The harness, not the agent, performs activation:

1. installs `requires.pip` packages
2. imports script skills and runs `selftest()` if present
3. on any failure, renames `SKILL.md` to `SKILL.md.failed` so the loader never sees it, and tells you

The agent has no shell access at any point. API keys belong in a `config.yaml` next to the handler, never in the skill code.
