# letta-ai/letta — PORT

The MemGPT reference. Two memory tiers: **core memory** = in-context labelled
`Block`s (`human`, `persona`) with a char `limit` and a `read_only` flag, kept
in the prompt; **archival/recall** = out-of-context, searched on demand. The
agent edits its own core memory via tools.

- **Stars/health:** 24.1k, active (2026-08) · **License:** Apache-2.0
  (vendorable)

## Does better than REMY
- Core-memory blocks are labelled and char-limited so they never blow the
  context budget — REMY's SOUL.md/USER.md have no size governor.
- A `read_only` flag per block — REMY could mark user-owned SOUL.md sections
  the agent must not overwrite.
- `conversation_search` (keyword/date-filtered over past turns) is exactly
  REMY's view (2) — and needs **no embeddings**.

## Read these files
- `letta-ai/letta@ff19ffe:letta/schemas/block.py:L18-46` — the `Block` schema:
  `value`, `limit`, `label`, `read_only`, `description`. The data model to copy
  for SOUL/USER blocks.
- `letta/schemas/memory.py:L68-170` — renders blocks into a `<memory_blocks>`
  prompt section with per-block `chars_limit` and `read_only` markers.
- `letta/functions/function_sets/base.py:L246-520` — the self-edit tools:
  `core_memory_append`, `core_memory_replace`, `rethink_memory`, `memory_insert`,
  `memory_replace`, `conversation_search` (keyword — no embeddings),
  `archival_memory_search` (semantic — skip).

## Lift
The `Block(value/limit/label/read_only)` model + the append/replace/rethink tool
set + keyword `conversation_search`. All map onto REMY's markdown files with no
new heavy deps.

## Avoid
Letta's full Postgres/ORM server stack and archival vector search — overkill for
a single-user Jetson.

## License constraint
Apache-2.0 — vendorable with attribution.

## Effort
**M** — port the block model + 4-5 edit tools; keep the files as markdown.
