# modelcontextprotocol/python-sdk — DEPEND

The official MCP Python SDK. Its high-level server class (recently renamed
`MCPServer`, formerly `FastMCP`) turns a decorated Python function into an MCP
tool in ~10 lines, stdio transport by default. This is the inversion REMY
needs: a `remy-mcp` stdio server exposing speak/notify/read-episodic-memory/
capture-camera-frame, listed in the same `--mcp-config` JSON as the external
servers, so the headless Claude session gets hands into REMY itself
(`mcp__remy__speak` etc.) instead of being a write-only file editor. Python
3.10+ — matches the Jetson exactly.

- **Stars/health:** 24k, active (2026-08) · **License:** MIT

## Does better than REMY
Handles the entire MCP protocol (initialize, tools/list, schema generation
from type hints, structured output, notifications, roots) so REMY writes only
plain functions.

## Read these files
- `modelcontextprotocol/python-sdk@a4f4ccd:examples/snippets/servers/mcpserver_quickstart.py:L7-42`
  — `from mcp.server.mcpserver import MCPServer`; `@mcp.tool()` on a typed
  function; `mcp.run(transport="streamable-http")` variant. Note the rename:
  older docs/blogs say `from mcp.server.fastmcp import FastMCP`.
- `modelcontextprotocol/python-sdk@a4f4ccd:examples/snippets/servers/direct_execution.py:L10-27`
  — minimal runnable server: `mcp = MCPServer("My App")`, `mcp.run()` defaults
  to stdio. This whole file is the REMY server skeleton.
- `examples/snippets/servers/structured_output.py`, `lifespan_example.py` at
  the same sha — typed results and startup/shutdown hooks (useful for opening
  the event-bus socket once per server process).

## Design note
The stdio server is spawned by `claude -p` as a child process, but REMY's
speakers/memory live in the resident app. Bridge with a tiny IPC: the MCP
server process connects to REMY's existing EventBus via a unix socket or
localhost TCP and publishes speak/notify events; memory reads go through the
same channel or direct file reads of `~/.remy/`. Keep the MCP process
stateless so a crashed session leaves nothing behind.

## Lift
One new file `remy/mcp_server.py` (entry point `python3 -m remy.mcp_server`)
with 4-6 `@mcp.tool()` functions; an mcp-config entry
`{"command": "python3", "args": ["-m", "remy.mcp_server"]}`; allowlist
`mcp__remy` in `--allowedTools`.

## Avoid
Importing heavy REMY modules (whisper, piper) into the MCP server process —
IPC to the resident app instead, per the defer-heavy-imports rule. SSE
transport (deprecated). Don't run streamable-http; stdio has zero port
management.

## License constraint
MIT — dependable, examples vendorable.

## Jetson cost
Pure-Python (anyio/pydantic/httpx deps). ~40-60MB RSS per spawned server
**ESTIMATE**, <1s startup, zero resident cost.

## Effort
**S** — the quickstart is the implementation.
