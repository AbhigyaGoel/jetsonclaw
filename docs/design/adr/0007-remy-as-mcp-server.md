# ADR 0007: REMY exposes its own tools to its agent as an MCP server

Status: proposed
Date: 2026-08-06

## Context

The agent can act on the world (files, web, soon Bash and MCP integrations) but
has no hands back into REMY. It cannot speak to the owner mid-task, post a
notification, read episodic memory, or capture a camera frame - all of which the
demos need. Demo 2 needs the agent to capture/see a rendered page; demo 4 needs
a long job to announce progress in REMY's voice; the credential grant flow (ADR
0004) needs the agent to trigger a spoken walk-through.

The Agent SDK provides two ways to give an agent local tools: in-process
`@tool` + `create_sdk_mcp_server` (`__init__.py:312-460`), and a normal stdio
MCP server via `--mcp-config`. Interactive sessions run inside REMY's process;
detached job runners (ADR 0002) are separate processes.

## Decision

REMY exposes a small, fixed set of its own capabilities to agent sessions:
`speak(text)`, `notify(text)`, `read_memory(query)`, `remember(fact)`,
`capture_frame()`, `screenshot(url_or_path)`, and a job-progress `report(text)`.

- Interactive in-process sessions use the SDK's in-process `@tool` server - no
  IPC, direct calls into REMY's speaker, workspace, and episodic store.
- Detached job runners (separate processes) reach the same capabilities through
  a thin stdio MCP server (`remy/mcp_server.py`) that talks to REMY over the
  same per-job event files and a local socket for speak/notify. The tool
  implementations are shared; only the transport differs.
- This server is also the hook for `--permission-prompt-tool mcp__remy__approve`
  later: permission decisions for dangerous calls can be routed through REMY's
  own voice-confirm instead of static allowlists.

## Rationale

- The agent needs to act on REMY (speak, remember, see) for three of the five
  demos; without it the agent is blind and mute to its own owner mid-task.
- Building it on the SDK's MCP surface reuses the same mechanism as external
  capability acquisition (ADR 0005) - one integration model, not two.
- Sharing tool implementations across the in-process and stdio transports keeps
  behavior identical whether a session is interactive or detached.

## Alternatives rejected

- Only the in-process `@tool` server. Rejected: detached job runners are
  separate processes and cannot use it; they need the stdio path.
- A bespoke RPC protocol between agent and REMY. Rejected: MCP is already the
  protocol the agent speaks; a second one is pure cost.
- Giving the agent direct Python access to REMY internals. Rejected: no
  boundary, and it could not work across the process split anyway.

## Consequences

- New `remy/mcp_server.py` and a shared `remy/agent_tools/` implementation
  module used by both transports.
- `speak`/`notify` from a detached runner must route through REMY (only REMY
  owns the speaker and the capture pause logic in `app.py:462-468`); the runner
  posts, REMY speaks. This keeps a single owner of the audio device.
- The permission-prompt-tool integration is deferred to after the broker and
  sandbox land, but the server is designed to host it.

## Verify on-box

- An interactive session calls `speak` and REMY talks without deadlocking the
  capture pause/resume.
- A detached runner's `report`/`speak` reaches REMY across the process boundary
  and is announced.
