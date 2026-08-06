# Anthropic memory tool + context editing — DEPEND (native Claude feature)

Not a repo — a native Claude capability, and REMY's agent *is* Claude Code, so
this is the closest-fitting memory design in the whole scan.

- **Source:** platform.claude.com docs — `memory_20250818` (GA on Claude 4+) and
  context editing (`clear_tool_uses_20250919`) · **License:** vendor feature,
  usable directly

## What it is
A client-side, file-based memory the model drives via 6 commands (`view`,
`create`, `str_replace`, `insert`, `delete`, `rename`) over a `/memories` dir.
The model checks memory before each task and writes what it learns; the app owns
storage. Context editing auto-clears oldest tool results past a token trigger
(default 100k), keeping the last N (default 3), and warns the model to save to
memory first.

## Does better than REMY
- The memory-write is a **first-class tool the agent calls deliberately** vs
  REMY's out-of-band idle consolidation — the model decides what's durable
  in-loop.
- A principled, token-triggered **eviction policy** REMY lacks (it just keeps
  "last few turns").
- `str_replace`/`insert` on files is exactly how a model should edit
  MEMORY.md/SOUL.md — line-addressable, idempotent, cheap, no embeddings.

## Read these
- The two live docs (memory tool + context editing). Load-bearing design: the
  auto-injected "ALWAYS VIEW YOUR MEMORY DIRECTORY FIRST / ASSUME INTERRUPTION"
  system prompt; the `str_replace` "must appear verbatim / reject on multiple
  occurrences" contract; the context-editing config (`trigger`/`keep`/
  `clear_at_least`/`exclude_tools`).

## Lift
Expose SOUL.md/USER.md/MEMORY.md editing to Claude Code via the same
`str_replace`/`insert` semantics + the "view memory first" discipline. If REMY
ever runs Claude over the API, enable `clear_tool_uses_20250919` for free
context management.

## Avoid
Nothing conceptually — but the memory tool is client-side, so REMY must
implement path-traversal protection (`/memories` prefix, canonicalize).

## License constraint
Native Claude feature — usable directly.

## Effort
**S** — REMY already has the markdown files; wiring the tool + system prompt is
small.
