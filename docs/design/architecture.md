# Target Architecture

How the new subsystems attach to what exists. The spine does not change: the
async `EventBus` (`events.py`) stays the one seam every surface subscribes to,
and `handle_text()` (`app.py:191`) stays the single entry point for voice, TUI,
dashboard, and stdin. The changes hang new subsystems off those two points and
move long agent work out of REMY's process.

## What exists today (unchanged in shape)

```
mic (arecord) -> wake (openWakeWord) -> STT (faster-whisper)
                                             |
                                             v
   TUI / PWA / stdin --------------------> handle_text() --_route_lock--> _route()
                                             |                              |
                                             v                              v
                                          EventBus <----------------- fast paths:
                                        (subscribers:                 intents, spotify,
                                         TUI, web /ws,                 dynamic skills,
                                         logs)                         local chat (ollama)
                                                                       agent (claude -p)
```

`_route` (`app.py:212-364`) is a fixed decision order: brief mode, confirmation
gate, follow-up window, then parsed intents (identity, brief.start, chat.reset,
memory, status, spotify, self.rollback, self.iterate/agent.task, agent.continue),
then hot-loaded skills, then the escalation lane (actionable-but-unhandled goes
to the agent to grow a skill), then local chat as the default.

## What changes

Five subsystems attach. None replaces the router; they extend the agent path,
the skill execution path, and add a job path alongside the in-process one.

```
                         handle_text() --_route_lock--> _route()
                                                          |
        in-process, fast (unchanged): intents, spotify, chat, quick skills
                                                          |
                                   long / capability work v
                                                   +--------------+
                                                   | Brain (SDK)  |  ADR 0001
                                                   | ClaudeSDKClient
                                                   | hooks->EventBus
                                                   | can_use_tool |
                                                   +------+-------+
                              interactive |                | detached
                                          v                v
                                  in-process session   Job engine  ADR 0002
                                  (@tool MCP, ADR 0007) sqlite table + systemd-run
                                          |                | --user units
                                          |                v
                                          |         remy/jobrunner.py (SDK, resume=id)
                                          |                |
                                          |         events.jsonl + heartbeat (per job)
                                          |                |
                                          +--------> EventBus <--- job watcher tails files
                                                          ^
   Capability registry (ADR 0005) --mcp-config-->        |
     github / google_workspace / playwright / filesystem |
   REMY MCP server (ADR 0007): speak/notify/memory/capture
   Credential broker (ADR 0004): 127.0.0.1 URL + bearer, refresh stays home
   Sandbox profiles (ADR 0003): bwrap A/B/C wrap every skill + toolchain exec
   Capture (ADR 0008): v4l2 frame / headless-shell screenshot -> disk -> Read
```

### Brain layer (ADR 0001)

`remy/brain/claude.py` keeps its `AgentLine`-shaped output but is reimplemented
on `ClaudeSDKClient`. New capabilities surface as new EventBus events (mapped
from SDK hooks) and as methods the orchestrator can call: send-into-session,
interrupt, resume-by-id. The old CLI path stays behind the interface, config-
selectable, until the SDK path passes selftest and an on-box resume test.

### Job engine (ADR 0002)

New `remy/jobs/` (sqlite store, state machine) and `remy/jobrunner.py` (the
process a unit runs). `_route` gains a branch: an agent request tagged
long-running creates a job row and launches a `systemd-run --user` unit instead
of running inside `_route_lock`. New intents cover "how's it going", "stop
that", and completion announcements come from a job watcher in the background
loop (`app.py:97-123`) that tails `events.jsonl`. The lock returns to guarding
only utterance routing.

### Capability registry + MCP (ADR 0005, 0007)

New `remy/capabilities/` (registry file, schema, `--mcp-config` composer) and
`remy/mcp_server.py` (REMY's own tools). A skill or agent request that needs an
integration pulls the server spec from the registry, composes a hermetic
`--mcp-config` with `--strict-mcp-config`, appends `mcp__<server>` to the
allowlist, and wires auth env from the broker.

### Credential broker (ADR 0004)

New `remy/secrets/` (age store, broker, grant flow). The skill loader
(`loader.py`) stops injecting raw `requires.env` secrets and instead injects a
broker URL and per-invocation bearer for `requires.credential`. Grant-needed
events drive the voice-plus-phone walk-through.

### Sandbox (ADR 0003)

New `remy/sandbox/profiles.py`. The loader routes all skill execution
(`loader.py:88-120`) through profile A instead of bare `bash -c` and in-process
import. Toolchain jobs run under profile C (the same systemd-run unit as the job
engine). Agent Bash uses Claude Code's own sandbox.

### Capture (ADR 0008)

Two small wrappers exposed as agent tools through the REMY MCP server. No new
subsystem.

## Data and control flow for one demo (demo 3: email -> calendar)

1. Voice: "add the thing from that email to my calendar." STT -> `handle_text`
   -> `_route` -> escalation lane (nothing local handles it) -> agent path.
2. Brain composes `--mcp-config` from the registry (`google_workspace` server),
   `--strict-mcp-config`, allowlist `mcp__gws`, auth env from the broker (a
   valid Google token, or a grant-needed event first).
3. Interactive SDK session: agent calls `mcp__gws__search_threads`,
   `mcp__gws__get_message`, extracts the event, calls
   `mcp__gws__create_event`, then `mcp__remy__speak("added it")`.
4. Hooks stream tool-use to the EventBus; TUI/PWA show progress; REMY speaks the
   result.

If the task were long (demo 4), step 3 runs in a `systemd-run` unit via
`jobrunner.py` with `resume=<session_id>`, progress goes to `events.jsonl`, and
the owner keeps talking to REMY meanwhile.

## Invariants preserved

- `EventBus` remains the only way components talk to surfaces (`events.py`); new
  subsystems publish, never reach into the TUI/web directly.
- `handle_text()` remains the single utterance entry; the job path is reached
  from inside `_route`, not by a second entry point.
- `python3 -m remy --selftest` stays the self-mod gate; every new subsystem adds
  tests so the gate actually covers it.
- The boot guard and crash-loop revert (`__main__.py:64-74`, `supervisor.py`)
  stay outside and above everything, unchanged.
- REMY stays MIT: every heavy or copyleft component (MCP servers, browser, age,
  bwrap) is a separate process, never linked in.
