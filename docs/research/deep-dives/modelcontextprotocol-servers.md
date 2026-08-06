# modelcontextprotocol/servers — DEPEND

The official MCP reference servers monorepo. After the 2025 archiving sweep
only seven remain: everything, fetch, filesystem, git, memory,
sequentialthinking, time (the old gdrive/gmail/github references live in the
archived repo — do not use them). The one that matters for REMY is
`filesystem`: a TypeScript stdio server with allowed-directory sandboxing and
dynamic MCP Roots support. Note REMY's `claude -p` already has Read/Write/Glob
/Grep built in, so filesystem-mcp only earns its spawn when a synthesized
skill needs file access *outside* the Claude session (or sandboxed subtrees
for a foreign agent).

- **Stars/health:** 89k, active (2026-08) · **License:** MIT -> Apache-2.0
  transition (both permissive)

## Does better than REMY
Canonical, spec-tracking implementations; `filesystem` shows the correct
allowed-dirs + roots/list_changed dance; `fetch` and `memory` are clean
patterns for tiny stdio servers.

## Read these files
- `modelcontextprotocol/servers@76d64c8:src/filesystem/index.ts:L45-93` —
  allowed directories resolved from argv, validated, then
  `setAllowedDirectories()`; the sandbox model in ~50 lines.
- `modelcontextprotocol/servers@76d64c8:src/filesystem/index.ts:L727-777` —
  roots protocol: on `roots/list_changed` the server refetches roots and
  replaces allowed dirs; falls back to argv dirs when client lacks roots.
  Claude Code answers `roots/list` with launch dir + `--add-dir` grants.
- `modelcontextprotocol/servers@76d64c8:src/filesystem/README.md:L27-33` —
  starting with no args and no client roots is a hard init error.
- `modelcontextprotocol/servers@76d64c8:src/filesystem/README.md:L244-258` —
  canonical config: `{"command": "npx", "args": ["-y",
  "@modelcontextprotocol/server-filesystem", "/allowed/dir"]}`.

## Lift
The `mcpServers` config idioms; the filesystem server itself when a demo needs
sandboxed FS access beyond the session's tools; `fetch`/`memory` as templates
for synthesized micro-servers.

## Avoid
Spawning filesystem-mcp when Claude Code's native Read/Write/Glob/Grep
suffice — it duplicates capability and burns ~60MB. Anything from
modelcontextprotocol/servers-archived (unmaintained since 2025-05).

## License constraint
MIT/Apache-2.0 — vendorable and dependable.

## Jetson cost
Node stdio process via npx: ~50-90MB RSS each **ESTIMATE**; npx cold start
~1-2s with warm cache. Node exists for arm64; all reference servers are pure
JS/Python, no native x86 deps.

## Effort
**S** — npx one-liner in mcp-config.
