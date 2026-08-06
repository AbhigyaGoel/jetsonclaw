# REMY Capability Program: Design

Target design for turning REMY from a voice assistant that can edit itself into
an autonomous agent that happens to have a voice. This directory is the output
of Phase 1 of the capability program and supersedes `docs/research/backlog.md`
as the planning document for capability work. (The backlog's voice-loop quality
items - turn detection, memory reconciliation, wake hardening - are orthogonal
and stay live there.)

Read `docs/research/blindspots.md` first for the research this design rests on,
and `docs/research/remy-briefing.md` for REMY as it exists today.

## The five acceptance demos

Done is defined by five end-to-end capability proofs, each spoken to the mic
with the keyboard untouched, each synthesized at runtime (no code written
specifically for the demo lives in `remy/`):

1. Index my favorited TikToks and write up my profile.
2. Show me three header variants for my portfolio, then push the second one.
3. Add the thing from that email to my calendar.
4. Get my CS104 repo, work the assignment, tell me when it's done.
5. Learn to do something novel, then do it.

A sixth, unannounced demo follows the fifth. The design targets that one.

## Documents

| File | What it decides |
|---|---|
| `architecture.md` | Target subsystems and how they attach to today's EventBus / handle_text / _route / skill harness |
| `migration.md` | Order of change that never leaves `main` unbootable |
| `ROADMAP.md` | Ordered milestones: capability, acceptance test, files, rollback, risk |
| `adr/0001-agent-sdk-over-cli.md` | Drive Claude via the Agent SDK, not a hand-rolled `claude -p` subprocess |
| `adr/0002-job-model.md` | Detached jobs as systemd-run user units + a sqlite job table |
| `adr/0003-sandbox-strategy.md` | bubblewrap as the one sandbox, three profiles |
| `adr/0004-credentials.md` | age-encrypted store + a broker that hands out short-lived tokens |
| `adr/0005-capability-acquisition.md` | Tools arrive as MCP servers written into `--mcp-config` at runtime |
| `adr/0006-topology.md` | Stay single-box; design for a future satellite split, do not build it |
| `adr/0007-remy-as-mcp-server.md` | REMY exposes its own tools (speak/memory/capture) to its agent |
| `adr/0008-vision-capture.md` | Two capture paths to disk; no resident VLM yet |

## The rule that orders everything

Every capability increase ships with the containment that makes it survivable,
in the same milestone. Bash and long unattended sessions do not land before the
sandbox and the watchdog that bound them. The roadmap is sequenced to honor
this, which is why the first two milestones buy no new demo - they are the
floor the demos stand on.

## Billing and auth (non-negotiable)

The economic model rides on staying subscription-backed. `claude-agent-sdk`
subprocesses the same `claude` CLI REMY already uses and inherits the same
subscription auth - it is not the Anthropic Messages API client and adds no
per-token billing. Anthropic paused a 2026-06-15 change that would have moved
`claude -p`/SDK usage onto a separate monthly credit; it may return, so the
model-invocation boundary stays behind one interface and any switch to API-key
billing is a config change, never a rearchitecture. `ANTHROPIC_API_KEY` must
never be set (it silently bills pay-as-you-go; `--doctor` asserts it). Cost is
measured from the `stream-json` result line into a ledger (`remy/cost.py`), not
guessed. Full text in `CLAUDE.md`.
