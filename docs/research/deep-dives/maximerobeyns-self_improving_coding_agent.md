# MaximeRobeyns/self_improving_coding_agent — PORT (steal the overseer)

A self-improving coding agent (ICLR 2025 workshop) that evaluates itself on
benchmarks, archives each version, and runs a separate **LLM "overseer"** that
watches the running agent's callgraph and can notify or forcefully cancel a
looping/stuck sub-agent.

- **Stars/health:** 378, active (2025-04) · **License:** MIT (vendorable)

## Does better than REMY
The overseer is a **live safety monitor**. REMY's crash-loop auto-revert is
*post-hoc* (revert after 3 boot fails); this catches looping/runaway behavior
*during* execution and cancels it — valuable for killing a Claude Code session
that's thrashing before it burns budget.

## Read these files
- `MaximeRobeyns/self_improving_coding_agent@ed8275d:base_agent/src/oversight/overseer.py:L42-165` —
  `OverseerJudgement`/`Overseer`: an `is_looping` detector with
  `force_cancel_agent` + `force_cancel_agent_id`, on a `check_interval`
  (default 60s).

## Lift
The overseer watchdog (loop-detection + forced cancel + notify-parent-with-
reason). Pairs with REMY's "one repair attempt" — the overseer decides when the
repair attempt is thrashing.

## Avoid
The LLM overseer's cost on-device — use a cheap heuristic instead (repeated
identical tool calls / wall-clock / token budget).

## License constraint
MIT — vendorable with attribution.

## Effort
**M** (or **S** for the heuristic version).
