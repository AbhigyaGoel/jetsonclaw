# acon96/home-llm — PATTERN-ONLY (the technique; not the code)

A Home Assistant integration + a family of small models (270M-3B) fine-tuned for
smart-home **function calling**. Directly relevant to REMY's qwen2.5:3b intent
path.

- **Stars/health:** 1.4k, active (2026-07) · **License:** no SPDX license
  (custom `LICENSES.txt`) — treat the **code** as PATTERN-ONLY; the prompt
  *technique* and the openly-licensed HF dataset/models are usable

## Does better than REMY
A proven, token-efficient prompt contract for making a 3B-class model emit
reliable structured tool calls, plus an in-context-learning fallback that gets
general models (explicitly Qwen) to function-call without fine-tuning. REMY
currently has no documented tool-serialization strategy for its qwen intent path.

## Read these files
- `acon96/home-llm@50cf35c:docs/Model Prompting.md:L6-28` — the system-prompt
  template: personality + time + `Tools: {{tools|to_json}}` + device list +
  in-context `<functioncall> {json}` examples.
- `docs/Model Prompting.md` (Prompt Variables) — three tool-serialization tiers:
  **Minimal** (`climate.set_hvac_mode(hvac_mode)` — fewest tokens), **Reduced**,
  full JSON. On REMY's CPU-bound token budget, Minimal is the right default.

## Lift
The `<functioncall>` prompt template + Minimal tool-serialization format for the
qwen intent path, using the ICL example approach (no fine-tuning — no RAM for a
second model). Fewer tokens = faster on CPU.

## Avoid
The HA custom_component and the llama.cpp fine-tuning path. Do **not** copy repo
code text (unclear license) — reimplement the technique.

## License constraint
No SPDX license — PATTERN-ONLY for code. Technique + openly-licensed HF dataset
are usable.

## Effort
**S** — a prompt-engineering change to REMY's existing qwen call.
