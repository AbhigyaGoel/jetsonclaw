# MineDojo/Voyager — PORT

The canonical skill-synthesis-with-self-verification loop, and the direct
ancestor of REMY's "give yourself a skill" flow. An LLM writes JS skills, stores
them in a vector-DB skill library, retrieves by embedding similarity, and
self-verifies each via a critic before accepting it.

- **Stars/health:** 7.1k, dormant (2024-04, ~16mo) · **License:** MIT
  (vendorable; code still directly liftable)

## Does better than REMY
- **Semantic skill retrieval.** REMY hot-loads all SKILL.md; Voyager embeds each
  skill's description and does top-k similarity retrieval — scales to hundreds
  of skills without stuffing them all into context.
- **Automatic curriculum.** A curriculum agent proposes the next skill to learn
  from current state; REMY's skills are user-driven only.

## Read these files
- `MineDojo/Voyager@55e45a8:voyager/agents/skill.py:L64-140` — `SkillManager`:
  skill store = `{code, description}` + Chroma vectordb; `add_new_skill`
  LLM-generates a description, versions collisions as `nameV2`, and asserts
  `vectordb.count() == len(skills)` (an integrity invariant to copy).
- `voyager/voyager.py:L285-296` — skill is committed **only on `success`**
  (`add_new_skill` gated by `info["success"]`) — REMY's selftest-gate analog.
- `voyager/voyager.py:L250-284` — the retry loop feeds `critique` into the next
  attempt (N critique-guided retries; REMY's single-repair budget is more
  conservative — good for on-device cost).

## Lift
The skill-library-as-vectordb + description-embedding retrieval + count
invariant; the critique-feedback retry shape.

## Avoid
The Minecraft env + critic specifics. Swap Voyager's OpenAI embeddings for a
local sentence-transformers embedder to avoid API calls.

## License constraint
MIT — vendorable with attribution.

## Jetson cost
Only if you add retrieval: a local embedder (MiniLM ~90MB resident) to weigh
against the 8GB budget. Worth it once skill count is high.

## Effort
**M** — the retrieval index + description generation is ~200 LOC; skip the
env/critic parts.
