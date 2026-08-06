# browser-use/browser-use — PATTERN-ONLY

The dominant "LLM drives a browser" agent (108k stars). Architecture: its own
agent loop (`Agent(task, llm)`) that snapshots the DOM, sends
state + screenshot to an LLM every step, and executes returned actions over
CDP via their `cdp-use` client (they dropped playwright). Two hard blockers
for REMY: (1) the loop requires a `BaseChatModel` backed by an API key
(`ANTHROPIC_API_KEY` / `OPENAI_API_KEY` / their paid ChatBrowserUse cloud) —
there is no way to run it against a Claude Code subscription session, which
violates REMY's no-API-billing constraint; (2) `requires-python >= 3.11`,
Jetson is Python 3.10. Ollama support exists but recommends 8B+ models; REMY's
qwen2.5:3b is below the bar and the Jetson has no RAM headroom for llama3.1:8b
alongside the resident stack.

- **Stars/health:** 108k, active (2026-08) · **License:** MIT

## Does better than REMY
Battle-tested prompts and DOM-serialization for browser agents: how to present
clickable elements to an LLM as indexed text, screenshot sizing per model
(`llm_screenshot_size` auto-config for Claude), judge/fallback LLM slots, step
timeouts, max-actions-per-step. Worth reading before REMY prompts its own
Claude session through playwright-mcp.

## Read these files
- `browser-use/browser-use@a3e3cc5:pyproject.toml:L6-50` —
  `requires-python = ">=3.11,<4.0"`; deps: `anthropic`, `openai`, `ollama`,
  `cdp-use` (no playwright); optional `browser-use-core` ships a
  linux/aarch64 wheel (so arm64 itself is fine)
- `browser-use/browser-use@a3e3cc5:browser_use/agent/service.py:L138-247` —
  Agent constructor: `llm: BaseChatModel`, `judge_llm`, `fallback_llm`,
  `step_timeout=180`, defaults to paid `ChatBrowserUse()` when no LLM given
- `browser-use/browser-use@a3e3cc5:browser_use/agent/system_prompts/` — the
  action-space prompt engineering to borrow

## Lift
- The system-prompt patterns (indexed interactive elements, "flash mode"
  terseness) as prior art for REMY's browser-skill prompt when driving
  playwright-mcp tools.
- The idea of a downscaled fixed `llm_screenshot_size` per model to cap
  vision-token cost.

## Avoid
- Depending on it: API-billed LLM loop (hard constraint violation) and
  Python >= 3.11 (Jetson is 3.10). Both are disqualifying today.
- Its MCP server mode still runs the paid loop underneath; it is not a
  tools-only browser server like playwright-mcp.

## License constraint
MIT. No obstacle — the blockers are runtime/economic, not legal.

## Effort
**S** to read and borrow prompts; **L** and rule-breaking to actually run it.
