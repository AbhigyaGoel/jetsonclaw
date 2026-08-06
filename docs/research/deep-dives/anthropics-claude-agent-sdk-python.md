# anthropics/claude-agent-sdk-python — DEPEND

Official Python SDK driving the Claude Code CLI as a subprocess. Since the last
scan it has grown from "typed permission gate" into a full job-engine substrate:
bidirectional streaming into a live session, resume-by-session-ID, session
forking, pluggable session stores, in-process MCP tools, Python hook callbacks,
and a CLI binary bundled inside the pip wheel (manylinux aarch64 included, so
the Jetson gets it from pip with no npm). This is the layer REMY should run
agent jobs through instead of raw `claude -p`.

- **Stars/health:** 7.8k, active (2026-08) · **License:** MIT · PyPI 0.2.131,
  `requires-python >= 3.10` (`pyproject.toml:10`), bundled CLI 2.1.223

## Capability answers (a-h)

**(a) Send a follow-up INTO a running session: YES.**
`ClaudeSDKClient.query()` writes a new user message onto the live subprocess
stdin at any time (`client.py:287-315`); `receive_messages()` keeps yielding.
"Owner says focus on part 2" is `await client.query("focus on part 2")`,
optionally preceded by `await client.interrupt()` (`client.py:317-321`) to
abort the current turn first.

**(b) Runtime tool gating: YES, with a shadowing trap.**
`can_use_tool: CanUseTool` (`types.py:257-260`) is an async callback
`(tool_name, input, ToolPermissionContext) -> PermissionResultAllow|Deny`.
Voice-confirm dangerous Bash = await a TTS confirm inside the callback.
`ToolPermissionContext` now carries `tool_use_id`, `title` (full prompt
sentence), `display_name`, `decision_reason` (`types.py:201-234`), ready-made
for speaking the prompt aloud. Trap: the callback only fires when permission
rules evaluate to "ask"; anything already allowed by `allowed_tools`,
`permission_mode`, or settings allow-rules skips it
(`types.py:1932-1948`, `CanUseToolShadowedWarning` at `types.py:1672-1727`).
To see every call, use a `PreToolUse` hook instead. Requires streaming mode
(string prompt raises, `client.py:161-167`).

**(c) Hooks for progress events: YES, as in-process Python callbacks.**
`hooks={HookEvent: [HookMatcher(matcher="Bash", hooks=[cb])]}`
(`types.py:1950-1961`, `HookMatcher` at `types.py:588-602`). Events:
PreToolUse, PostToolUse, PostToolUseFailure, UserPromptSubmit, Stop,
SubagentStop, PreCompact, Notification, SubagentStart, PermissionRequest
(`types.py:263-274`). Callbacks are plain async Python invoked over the
control protocol, so a PostToolUse hook can publish straight onto REMY's
EventBus (job heartbeat + progress in ~10 lines). Alternative:
`include_hook_events=True` emits hook lifecycle events in the message stream
(`types.py:1972-1978`). Matchers on the same event fire concurrently, do not
assume ordering (`types.py:1956-1960`).

**(d) Resume by ID after restart: YES. fork_session: YES.**
`resume: str` takes a session ID (`types.py:1827-1828`) and is passed as
`--resume=<id>` (`subprocess_cli.py:629-637`), unlike `--continue`'s
most-recent-only (`continue_conversation`, `types.py:1823-1825`).
`fork_session=True` resumes into a NEW session ID, leaving the original
untouched (`types.py:1980-1982`, `--fork-session` at `subprocess_cli.py:691-692`).
Persist the session_id from the init/result messages into the job row; after a
REMY crash, `ClaudeSDKClient(options=...(resume=job.session_id))` reattaches
the full conversation. There is also a `SessionStore` protocol
(`types.py:1485-1580`) that mirrors every transcript line to an external store
and can materialize a resume from it into a temp `CLAUDE_CONFIG_DIR`
(`session_resume.py:1-90`); local-disk JSONL is fine for REMY, so this is
optional. `list_sessions()`-style metadata (`SDKSessionInfo`,
`types.py:1588-1609`) gives summary/first-prompt/cwd per session.

**(e) In-process MCP tools: YES.**
`@tool(name, desc, schema)` + `create_sdk_mcp_server(name, tools=[...])`
(`__init__.py:171-229`, `312-460`) runs an MCP server inside REMY's process,
no subprocess, direct access to REMY state. speak/notify/memory-write become
`mcp__remy__speak` etc. Passed via `mcp_servers={"remy": server}`; the SDK
strips the instance and routes calls over the control protocol
(`client.py:197-202`).

**(f) Subscription OAuth: YES.**
The subprocess inherits the parent env (minus `CLAUDECODE`) and merges
`options.env` (`subprocess_cli.py:786-797`); `CLAUDE_CODE_OAUTH_TOKEN` flows
through exactly as with the CLI. Nothing forces an API key; auth is entirely
the CLI's. `session_resume.py` even copies OAuth `.credentials.json` into the
temp config dir for store-backed resume.

**(g) Spawns the CLI: YES, but the wheel bundles it.**
`_find_bundled_cli()` looks for `_bundled/claude` inside the package first
(`subprocess_cli.py:247-343`); PyPI ships
`claude_agent_sdk-0.2.131-py3-none-manylinux_2_17_aarch64.whl` with CLI
2.1.223 (`_cli_version.py:3`), falling back to PATH `claude`. Minimum CLI
2.0.0 enforced by a version probe (`subprocess_cli.py:36`, `1126-1158`).
Overhead vs raw `claude -p`: none that matters, it is the same one CLI
subprocess per session (**ESTIMATE** 200-400MB RSS for the CLI process, same
as today) plus a thin anyio read loop. Deps: `anyio>=4`, `mcp>=1.23`
(`pyproject.toml:27-31`).

**(h) Options grab-bag.**
`include_partial_messages=True` -> `--include-partial-messages`, streaming
deltas for live TTS (`types.py:1966-1970`). `interrupt()` per (a).
`max_turns` (`types.py:1837-1841`), `max_budget_usd` (`types.py:1843-1848`),
`permission_mode` literals now include `dontAsk` and `auto` (model-classifier
approval) (`types.py:25-27`). Also: `set_permission_mode()` /
`set_model()` mid-session (`client.py:323-372`), `rewind_files()` with
`enable_file_checkpointing=True` (`client.py:374-404`, `types.py:2089-2095`),
`get_context_usage()` (`client.py:510-544`), `env`, `cwd`, `max_buffer_size`,
`stderr` callback, `settings`, `setting_sources`, `agents`, `skills`,
`sandbox`, `output_format` (JSON schema structured output), `thinking` /
`effort` controls (`types.py:1790-2120`).

## Does better than REMY
Everything REMY's raw `claude -p` wrapper does, plus mid-session input,
interrupt, resume-by-ID, fork, per-call permission gating with speakable
prompt text, in-process tools, and Python hook callbacks. Kills REMY's
"600s per-line-read, --continue only, no follow-up" ceiling in one dependency.

## Read these files
- `anthropics/claude-agent-sdk-python@71142da:src/claude_agent_sdk/client.py:L287-321` — `query()` into a live session + `interrupt()`
- `@71142da:src/claude_agent_sdk/types.py:L1823-1848` — `continue_conversation` vs `resume` vs `session_id`, `max_turns`, `max_budget_usd`
- `@71142da:src/claude_agent_sdk/types.py:L1932-1961` — `can_use_tool` semantics and the shadowing trap; `hooks`
- `@71142da:src/claude_agent_sdk/types.py:L201-260` — `ToolPermissionContext` (title/display_name for voice), `PermissionResultAllow/Deny`
- `@71142da:src/claude_agent_sdk/types.py:L263-274` — full `HookEvent` literal set
- `@71142da:src/claude_agent_sdk/__init__.py:L312-460` — `create_sdk_mcp_server` in-process MCP
- `@71142da:src/claude_agent_sdk/_internal/transport/subprocess_cli.py:L629-692` — `--resume=`/`--session-id=`/`--fork-session` flag building (note injection guard)
- `@71142da:src/claude_agent_sdk/_internal/transport/subprocess_cli.py:L247-343` — bundled-CLI discovery order
- `@71142da:src/claude_agent_sdk/_internal/transport/subprocess_cli.py:L786-797` — env inheritance (OAuth token passes through)
- `@71142da:src/claude_agent_sdk/_internal/session_resume.py:L1-90` — SessionStore materialization into temp CLAUDE_CONFIG_DIR

## Lift
Replace REMY's hand-rolled `claude -p` subprocess with `ClaudeSDKClient` for
agent jobs: `resume` for crash recovery (session_id in the job row),
`interrupt()` + `query()` for voice redirects, `can_use_tool` for voice
confirmation, one PostToolUse hook publishing to EventBus for heartbeat and
"how's it going", `create_sdk_mcp_server` for speak/notify.

## Avoid
`allowed_tools`/`bypassPermissions` silently shadowing `can_use_tool`; string
prompts with `can_use_tool` (raises); assuming hook matcher ordering; the
SessionStore machinery (local JSONL suffices); relying on the client across
async contexts (one anyio task group from connect to disconnect,
`client.py:59-65`). The SDK client is in-process: the CLI subprocess dies with
REMY, so detached jobs still need a separate runner process (systemd-run) with
the SDK inside it.

## License constraint
MIT, dependable. `mcp` dep is MIT.

## Jetson cost
Pure-Python + bundled aarch64 CLI binary in the wheel (**ESTIMATE** wheel
~50-100MB on disk for the binary; runtime RSS same as today's `claude -p`).

## Effort
**M**: swap `remy/brain/claude.py` to `ClaudeSDKClient`, wire hooks to
EventBus, store session_id per job.
