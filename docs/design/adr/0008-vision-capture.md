# ADR 0008: Two capture paths to disk; no resident VLM yet

Status: proposed
Date: 2026-08-06

## Context

There is no capture path anywhere in the tree - no camera, no screenshot, no
image into the agent. The program brief lists sight as a ceiling. But the
agent's allowed tools include Read (`config.py:88`), and Claude Code's Read
ingests PNG/JPG natively, so the agent can already see any image on disk. The
gap is producing images, not seeing them.

Research (`docs/research/deep-dives/`: vikhyat-moondream,
blakeblackshear-frigate, rapidai-rapidocr, nvidia-ai-iot-nanoowl,
dusty-nv-jetson-inference) found that 3B-class VLMs on this board post 0.5-1.1
tokens/sec, and everything NVIDIA-branded (nanoowl, jetson-inference,
DeepStream) wants ~2GB resident PyTorch+TRT for detection the agent gets free by
Reading an image. Demo 2 (render three variants, choose one) needs zero new ML.

## Decision

Add two capture paths that each land a file on disk for the agent to Read. Do
not add a resident vision model.

- Camera one-shot: `v4l2-ctl --stream-mmap --stream-skip=5 --stream-count=1
  --stream-to=/tmp/frame.jpg` (UVC MJPEG frames are valid JPEGs; the skip
  discards auto-exposure warm-up). Exposed as the `capture_frame()` agent tool
  (ADR 0007), zero resident cost.
- Rendered-HTML screenshot: `chrome-headless-shell --headless --screenshot`, or
  the playwright-mcp `browser_take_screenshot` when a browser task is already
  up. Exposed as `screenshot(...)`.

A local VLM is admitted only when a continuous or offline vision feature is
actually scheduled, and then it is `ollama pull moondream` (1.7GB, transient via
`keep_alive:0`), gated in front by frigate's ~80-line motion detector (MIT,
pattern port) - never a resident model. OCR is an optional RapidOCR skill
(numpy<2 safe) for verbatim/offline needs only; default document reading stays
with the agent's Read.

## Rationale

- Ingestion already exists, so sight collapses to two small capture wrappers,
  not a vision subsystem. This is the cheapest path that satisfies the demos.
- The decision rule from research: user-initiated, one-shot, quality-sensitive
  vision goes frame-to-disk-then-Read; only continuous/gating/offline vision
  justifies a local model, and this program has none of that.
- Refusing a resident VLM protects the 8GB budget and the single-box decision
  (ADR 0006).

## Alternatives rejected

- A resident local VLM (qwen2.5vl, LLaVA). Rejected: 0.5-1.1 tok/s on this
  board and evicts qwen from RAM.
- NVIDIA nanoowl/jetson-inference/DeepStream. Rejected: RAM-for-value fails; the
  agent's Read answers the same questions for free.

## Consequences

- New dep: `v4l-utils` (apt, arm64). The screenshot path reuses the browser
  stack from ADR 0005/0006.
- If OpenCV ever enters (motion gate), pin
  `opencv-python-headless==4.11.0.86`; later wheels require numpy>=2 and would
  brick tflite-runtime (a hard constraint).
- Vision latency for a user-initiated shot is capture (~1s) plus session
  inference; acceptable because the owner is already waiting for the answer.

## Verify on-box

- The C720 produces a valid JPEG via v4l2-ctl with the warm-up skip.
- The agent Reads that JPEG and answers about it within the latency budget.
