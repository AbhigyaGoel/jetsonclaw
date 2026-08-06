# dusty-nv/jetson-containers — DEPEND

The canonical build/registry system for arm64 Jetson containers. Ships prebuilt
r36 images on Docker Hub (`dustynv/*`) for every core REMY model.

- **Stars/health:** 4.8k, active (2026-08) · **License:** Apache-2.0* (repo
  header NOASSERTION; per-package licenses mostly Apache-2.0/MIT — verify per
  file before vendoring)

## Which of REMY's models have ready-made r36 arm64 images (stop building from source)
- **ollama** → `dustynv/ollama:0.5.7-r36.4.0` / `:r36.4.0` (CUDA, arm64).
- **faster-whisper** → `dustynv/faster-whisper:r36.4.0-cu128-24.04` (arm64).
- **piper** → `piper1-tts:1.3.0` (note: piper1-tts embeds espeak-ng → **GPL**;
  keep Piper a separate-process sidecar, not linked, to protect REMY's MIT — or
  use the older `piper-tts` wheel).
- **openWakeWord** → `dustynv/wyoming-openwakeword:latest-r36.2.0`.
- Plus TensorRT, llama_cpp, mlc, vllm, transformers r36 packages.

## Does better than REMY
`packages/smart-home/wyoming/docker-compose.yaml` composes a **complete prebuilt
voice pipeline** — `wyoming-openwakeword` + `wyoming-whisper` + `wyoming-piper` +
`assist-microphone`, exactly REMY's stack, already arm64/r36, wired over the
Wyoming protocol. Cleaner IPC than in-process coupling and enables per-model
container memory isolation.

## Read these files
- `dusty-nv/jetson-containers@70c149a:packages/smart-home/wyoming/docker-compose.yaml` — the full arm64 voice
  pipeline (image tags, `/dev/snd` sharing).
- `packages/llm/ollama/docs.md:L55-90` — memory table + run command.
- `packages/speech/faster-whisper/config.py`, `packages/speech/piper1-tts/config.py` — pinned versions + the piper1 GPL note.

## Lift
Pull `dustynv/*:*-r36.x` images directly; adopt the Wyoming compose as REMY's
process topology.

## Avoid
Compiling whisper/piper/ollama from source. Note: **no model-swap orchestrator
exists here** — the memory-pressure problem is unsolved (see gaps.md).

## Vision addendum (2026-08)
- The ollama images above also serve **vision** models: `moondream:1.8b`
  (1.7GB) fits REMY's budget transiently; `qwen2.5vl:3b`/`gemma3:4b`
  (~3.2-3.3GB dl, **ESTIMATE** 4-5GB resident) only fit with qwen2.5:3b
  unloaded first — ollama is already REMY's model-swap mechanism
  (`keep_alive:0`).
- jetson-ai-lab archive benchmarks (Orin Nano Super): SmolVLM-2B 12.9 tok/s;
  VILA-1.5-3B 1.06 t/s; LLaVA-1.6-7B 0.57 t/s — the 3B+ VLM class is
  effectively unusable interactively; sub-2B is the only viable local tier.
- The `nano_llm`/NanoVLM packages target dusty-nv/NanoLLM (last push 2024-10,
  effectively unmaintained) — prefer the ollama images.

## License constraint
Per-package (mostly Apache-2.0/MIT; piper1-tts GPL — sidecar only).

## Jetson cost
Images ~3-5GB each on disk; no extra runtime RAM.

## Effort
**M** — containerize REMY around these.
