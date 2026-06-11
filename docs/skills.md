# Skills

A skill is a directory under `~/.remy/skills/` containing a `SKILL.md`. Skills are rescanned on every utterance with an mtime cache, so new or edited skills take effect immediately. No restart, no redeploy.

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
| `action.command` | shell snippet; the utterance is in `$REMY_TEXT`; stdout is spoken |
| `action.script` | a Python file in the same directory exposing `handle(text) -> str` |
| `requires.bins` | binaries that must exist or the skill is hidden |
| `requires.env` | env vars that must be set or the skill is hidden |
| `requires.pip` | pip packages the harness installs on activation |
| `watch.interval_secs` | run on a schedule; see watchers below |
| `inject` | keywords that push the markdown body into chat context |

## Knowledge skills

A SKILL.md with `inject` keywords and no action is pure knowledge. When an
utterance contains a keyword, the body is injected into the chat system
prompt for that turn:

```markdown
---
name: house
description: facts about the house
inject: [thermostat, heating, boiler]
---
The thermostat is in the hallway. Never set it above 23C.
The boiler reset switch is behind the left panel.
```

## Follow-ups

Script skills may define `converse(text) -> str | None`. After a skill
handles an utterance, it gets first refusal on the next one for two minutes.
Return a string to answer, or None to decline and let normal routing run.
This is what makes multi-turn skills (quizzes, step-by-step flows) work
without any LLM routing.

## Watchers

Add a `watch` block and the skill runs on a schedule instead of (or in addition to) voice triggers:

```markdown
---
name: ci-watch
description: announce CI failures on my repo
watch:
  interval_secs: 300
action:
  command: gh run list -R you/repo -L 1 --json conclusion,displayTitle --jq '.[] | select(.conclusion=="failure") | "CI failed: " + .displayTitle'
requires:
  bins: [gh]
---
```

Rules: minimum interval 60 seconds, empty output means stay silent, and the assistant only speaks when the output **changes**. It will tell you the build broke once, not every five minutes. Watchers never interrupt an in-flight conversation.

"Give yourself a watcher that tells me when ..." produces one of these.

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
