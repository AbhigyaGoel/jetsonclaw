# vikhyat/moondream — DEPEND (process boundary; the one local VLM to admit)

Tiny VLM (2B primary, 0.5B distilled) built for exactly REMY's hardware class.
If REMY ever needs local vision without a Claude session, this is the single
model worth admitting: `ollama pull moondream` is 1.7GB on disk and the ollama
server REMY already runs serves it — zero new processes, zero new deps.

- **Stars/health:** 9.9k, active (2026-04) · **License:** Apache-2.0

## Does better than REMY
REMY has no offline vision at all. Moondream does captioning, VQA, OCR-ish
reading, and object detection ("point at X") in ~2GB — the only VLM class that
coexists with faster-whisper + qwen2.5:3b + piper on an 8GB shared-memory board.

## Read these files
- `vikhyat/moondream@6eccfce:README.md:L18-21` — 2B primary / 0.5B edge-distill
  variants.
- `vikhyat/moondream@6eccfce:sample.py:L1-40` — HF transformers usage
  (`vikhyatk/moondream2`, revision-pinned); shows the torch path REMY should
  NOT take (torch + transformers resident is too heavy).

## Lift
- `ollama pull moondream` (1.7GB), call via the same `/api/generate` REMY uses
  for qwen2.5:3b, with `images:[base64]` and `keep_alive:0` so it unloads after
  each answer. Resident only during the call: **ESTIMATE** ~2.2-2.5GB, ~3-6s
  cold-load, a few tokens/sec on Orin Nano (no published figure; SmolVLM-2B
  does 12.9 tok/s on the Super per jetson-ai-lab, moondream should be similar
  order).
- Use as the semantic tier of wake-on-vision: frame-diff gate (free) → moondream
  "is a person present / what changed" (seconds, offline) → Claude session only
  for real conversations.

## Avoid
- The repo's torch/transformers path — pulls PyTorch onto the board for nothing.
- Note the ollama-library `moondream` is a ~2-year-old moondream2 revision;
  newer revisions (better OCR/pointing) need a community GGUF or HF. Good
  enough for gating, not for reading documents (Claude or RapidOCR do that).

## License constraint
Apache-2.0 — clean. Served over HTTP by ollama: DEPEND, no vendoring.

## Jetson cost
1.7GB disk; RAM only while loaded (keep_alive:0). **ESTIMATE** ~2.3GB transient.

## Effort
**S** — one ollama pull + ~30 lines in `remy/brain/ollama.py` to pass images.
