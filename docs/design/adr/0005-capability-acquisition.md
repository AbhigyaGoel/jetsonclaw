# ADR 0005: Tools arrive as MCP servers written into --mcp-config at runtime

Status: proposed
Date: 2026-08-06

## Context

The thesis is that when the owner asks for something REMY cannot do, REMY
acquires the ability. Today the only acquisition path is solve-then-absorb
(`app.py:389-412`): the agent writes a workspace skill, the harness activates
it. That works for skills built from REMY's existing tools (Read/Edit/Write/
Grep/WebFetch and, soon, sandboxed Bash), but not for capabilities that need a
real integration surface - Gmail, Calendar, GitHub, a browser.

`claude.mcp_config` is already plumbed into the agent invocation
(`config.py:91`, wired at `claude.py:45-46`) and defaults empty. Research
(`docs/research/deep-dives/`: github-github-mcp-server,
taylorwilsdon-google_workspace_mcp, modelcontextprotocol-servers,
modelcontextprotocol-python-sdk, microsoft-playwright-mcp) and the current
Claude Code docs established:

- Each `claude -p` / SDK spawn is a fresh process that reads `--mcp-config` at
  startup. A synthesized skill can add a tool by writing the JSON and letting
  the next spawn pick it up. No CLI change, no trust prompt, provided REMY also
  passes `--strict-mcp-config` (which ignores project `.mcp.json` and its
  interactive approval gate, making each spawn hermetic).
- Tools are named `mcp__<server>__<tool>`; `--allowedTools mcp__<server>`
  allowlists a whole server.
- Healthy stdio servers exist for the demo surfaces, all arm64-clean:
  github-mcp-server (official, MIT, prebuilt arm64 binary),
  google_workspace_mcp (MIT, one server for Gmail+Calendar+Drive, LAN-
  configurable OAuth callback - the only healthy Gmail path), the filesystem
  reference server, playwright-mcp for the browser.

## Decision

Capability acquisition is a config write plus an allowlist append plus a
respawn. REMY owns a capability registry that a synthesized skill can extend.

- A registry file (`~/.remy/capabilities.json` or similar) maps a capability
  name to an MCP server spec (command/args/env or url) and the auth it needs.
- A skill manifest declares `requires.capability: <name>`. When REMY spawns an
  agent for that skill, it composes the `--mcp-config` from the registry
  entries the skill needs, appends `mcp__<server>` to `--allowedTools`, wires
  the server's auth env from the broker (ADR 0004), and always passes
  `--strict-mcp-config`.
- Acquiring a new capability at runtime = the agent (or a curated catalog step)
  writes a vetted registry entry; the next spawn has the tool. The catalog of
  known-good servers is curated in the repo, not discovered arbitrarily from the
  internet, so a misheard request cannot install a hostile server.
- REMY also runs its own MCP server (ADR 0007) so the agent has hands back into
  REMY.

## Rationale

- The mechanism the thesis needs already exists in the CLI/SDK; what is missing
  is a registry, the broker wiring, and the discipline (`--strict-mcp-config`,
  curated catalog) around it.
- MCP servers are process-boundary integrations, so a GPL/AGPL server is fine to
  run without touching REMY's MIT license.
- Curating the catalog rather than letting the agent install arbitrary servers
  keeps the security story bounded while still allowing runtime acquisition of
  anything on the vetted list.

## Alternatives rejected

- Hand-rolled Python client libraries per provider inside skills. Rejected:
  reinvents maintained MCP servers, multiplies auth code, and puts secrets in
  more places.
- Fully open-ended runtime server install (agent pip-installs and configures any
  MCP server it finds). Rejected for now: too much attack surface for a voice-
  triggered system; revisit once the sandbox and broker are proven.
- Remote HTTP MCP servers with interactive OAuth. Rejected for headless use:
  their auth needs `/mcp` interactive login; stdio servers with env/token auth
  fit better.

## Consequences

- New: a capability registry module and schema, and a manifest
  `requires.capability` field the loader understands.
- Node must be present for node-based servers (fine on arm64); the github
  server ships a native arm64 binary.
- RAM is on-demand per spawn, zero resident (ESTIMATE: gh 25-50MB, node servers
  50-90MB, workspace-mcp 120-200MB, playwright+chromium 400-700MB) - browser
  tasks require unloading the ollama model first on 8GB (see ADR 0006).

## Verify on-box

- A registry-driven `--mcp-config` + `--strict-mcp-config` spawn connects the
  server and the agent can call `mcp__<server>__<tool>` under the appended
  allowlist.
- google_workspace_mcp completes its OAuth with the callback pointed at the
  Jetson's LAN address and the owner's phone.
- Writing a new registry entry between two spawns makes the tool available on
  the second with no restart of REMY.
