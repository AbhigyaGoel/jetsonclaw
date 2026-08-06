# mem0ai/mem0 — VENDOR (prompts)

A two-stage LLM memory pipeline: (1) **extract** atomic facts from a turn,
(2) **consolidate** against existing memories by emitting ADD/UPDATE/DELETE/NONE
ops, so the store stays deduplicated and current.

- **Stars/health:** 62.6k, active (2026-08) · **License:** Apache-2.0
  (prompts are the vendorable asset)

## Does better than REMY
REMY's idle pass "summarizes each day and folds durable facts in" but has **no
reconciliation** — it appends and never retracts, so MEMORY.md accumulates stale
and contradictory facts ("favorite color: blue" stays when it becomes "green").
mem0's UPDATE/DELETE step is exactly the missing piece, and it needs no
embeddings for the LLM-only path.

## Read these files
- `mem0ai/mem0@3f39fba:mem0/configs/prompts.py:L11-60` —
  `FACT_RETRIEVAL_PROMPT`: extracts user facts as JSON `{"facts":[...]}`,
  user-messages-only. Runs on qwen2.5:3b.
- `:L176-320` — `DEFAULT_UPDATE_MEMORY_PROMPT`: the ADD/UPDATE/DELETE/NONE
  reconciliation prompt with worked examples. This is the logic to bolt onto
  REMY's idle pass.
- `:L464-520` — V3 additive extraction + `linked_memory_ids`: link related
  memories without a graph DB.

## Lift
The extract + reconcile prompts (close to verbatim), run on qwen2.5:3b during
the idle pass, writing ops into MEMORY.md.

## Avoid
mem0's default vector store + embedding retrieval — on 8GB a resident embedder
(bge-small ~130MB up to nomic ~1GB) competes with whisper+qwen+piper. Keep
REMY's keyword search.

## License constraint
Apache-2.0 — vendorable with attribution.

## Jetson cost
Zero new deps for the prompt path (reuses resident qwen2.5:3b).

## Effort
**S** — a prompt + a JSON-op parser in the idle pass.
