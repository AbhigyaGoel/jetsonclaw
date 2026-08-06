# ADR 0001: Drive Claude with the Agent SDK, not a hand-rolled CLI subprocess

Status: accepted — scaffolding landed 2026-08-06 (M1); on-box benchmark gate pending
Date: 2026-08-06

## Context

Today `remy/brain/claude.py` spawns `claude -p` with
`asyncio.create_subprocess_exec`, parses `stream-json` lines by hand
(`claude.py:97-120`), and exposes an `AgentLine(kind, text)` stream to the rest
of the app. It has exactly one resume mode, `--continue` (most recent session
in the workdir, `claude.py:43-44`), one timeout applied per stdout line read
(`claude.py:71-72`), and no way to send a message into a running session, gate
an individual tool call, or receive structured progress except by scraping
text.

The capability program needs all of those. Detached 30-minute jobs
(demo 4) must be resumable by a specific ID after REMY restarts itself.
Voice-confirming a dangerous tool call (giving the agent Bash) needs per-call
gating. Progress-on-request ("how's it going?") needs structured events, not
text scraping. Mid-session steering ("focus on part 2") needs an input channel
into a live session.

`anthropics/claude-agent-sdk-python` (MIT, 7.8k stars, active) provides every
one of these. Verified at source (citations in
`docs/research/deep-dives/anthropics-claude-agent-sdk-python.md`):

- Resume by session ID: `resume=<id>` -> `--resume` (`types.py:1827`), plus
  `fork_session` (`types.py:1980`).
- Send into a live session: `client.query()` writes live stdin
  (`client.py:287-315`); `interrupt()` (`client.py:317-321`).
- Per-call gating: `can_use_tool` async callback (`types.py:201-260`).
- Progress hooks: in-process async Python hooks for PreToolUse/PostToolUse/Stop
  etc. (`types.py:263-274`) that map straight onto the EventBus.
- In-process MCP tools: `@tool` + `create_sdk_mcp_server` (`__init__.py:312-460`).
- Subscription auth: the subprocess inherits env, so
  `CLAUDE_CODE_OAUTH_TOKEN` flows through unchanged (`subprocess_cli.py:786-797`).
  No API key is forced.
- Jetson fit: pure Python, requires >=3.10, and the aarch64 wheel bundles the
  `claude` binary (`subprocess_cli.py:247-343`), removing the npm install step.

## Decision

Adopt `claude-agent-sdk` as the engine under `remy/brain/`. Keep the existing
`AgentLine`-shaped interface that `app.py` consumes so the orchestrator does not
churn; reimplement it on top of `ClaudeSDKClient` and map SDK message/hook
events to `AgentLine(kind, text)` plus new richer events where they earn their
keep.

The raw-CLI path stays behind the same interface as a fallback, selectable by
config, until the SDK path has run the full selftest and a manual resume test on
the Jetson.

## Rationale

- One dependency removes four hand-rolled mechanisms (subprocess lifecycle,
  stream-json parsing, resume, timeout) and unlocks four the program needs.
  This is exactly the "prefer deleting REMY's hand-rolled machinery" rule.
- It is the substrate the job model (ADR 0002) and the permission story (ADR
  0004, ADR 0007) build on. Deciding it first prevents rework.
- Pure-Python, subscription-auth, py3.10, bundled CLI: it clears every hard
  constraint.

## Alternatives rejected

- Keep the CLI wrapper and add resume/gating by hand. Rejected: reimplements
  the SDK badly, and `--resume`-by-id plus `can_use_tool` are non-trivial to
  fake over stdout scraping.
- LangChain/other agent frameworks. Rejected: they want an API key billing
  model, contradicting the Max-subscription constraint, and add far more than
  REMY uses.

## Consequences

- New dep `claude-agent-sdk` (pure Python; RSS of a session is the same as
  today's `claude -p`, ESTIMATE 200-400MB, benchmark on-box).
- A `ClaudeSDKClient` instance is bound to one async context between
  connect and disconnect (`client.py:59-65`); the brain layer must own the
  lifecycle, not pass clients across tasks.
- `--selftest` must gain a test that imports the SDK and runs a trivial session
  against a stub, so a broken upgrade is caught by the self-mod gate.
- `can_use_tool` is shadowed by `allowed_tools`/`bypassPermissions`
  (`types.py:1932-1948`); the brain must not set those when it wants the gate.

## Verify on-box

- SDK session RSS and cold-start latency vs today's CLI.
- `--resume=<id>` actually re-attaches to a session created before a restart.
- Bundled-CLI wheel installs and runs on JetPack r36 aarch64.
