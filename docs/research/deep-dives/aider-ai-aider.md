# Aider-AI/aider — VENDOR

Production pair-programmer. Its **repo-map** builds a token-budgeted, ranked
summary of a whole repo using tree-sitter symbol extraction + PageRank over the
def/ref graph, so the LLM gets cheap whole-repo context without reading every
file.

- **Stars/health:** 48.0k, active (2026-05) · **License:** Apache-2.0 (vendorable)

## Does better than REMY
REMY's self-edit sessions lean on Claude Code's own file discovery. Aider's
repo-map is a proven, cheaper way to hand the agent "here's the shape of the
codebase and the most relevant symbols" up front, budgeted to a token cap and
personalized toward the files the request mentions.

## Read these files
- `Aider-AI/aider@5dc9490:aider/repomap.py:L42-101` — `RepoMap`: `map_tokens`
  budget, `token_count`, disk-cached tags, scaled to fit `max_context_window`.
- `:L365-470` — `get_ranked_tags`: a `networkx.MultiDiGraph` of defines/
  references with **PageRank personalized toward files/idents in the request**
  (`personalize = 100/len(fnames)`).
- `:L233-279` — `get_tags`/`get_tags_raw`: tree-sitter tag extraction + caching.

## Lift
The tree-sitter-tags + PageRank-ranked, token-budgeted repo-map, fed as a
preamble to each headless Claude Code self-edit session, personalized toward the
skill/module the user asked to change. REMY's repo is small, so this is cheap
even on the Jetson.

## Avoid
Coupling to aider's `io`/`model` objects — budget a day to decouple `repomap.py`
from the rest of aider.

## License constraint
Apache-2.0 — vendorable with attribution/NOTICE.

## Jetson cost
Deps `grep-ast`, `tree-sitter`, `tree-sitter-language-pack`, `networkx`,
`diskcache`, `pygments` — all pip, arm64-friendly, no GPU, ~tens of MB.

## Effort
**M** — `repomap.py` is fairly self-contained but pulls the tree-sitter stack.
