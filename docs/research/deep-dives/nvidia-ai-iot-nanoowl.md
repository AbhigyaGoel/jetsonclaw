# NVIDIA-AI-IOT/nanoowl — IGNORE (open-vocab detection REMY doesn't need resident)

TensorRT-optimized OWL-ViT: open-vocabulary object detection ("an owl, a
glove") claimed real-time on Jetson Orin. Impressive, Apache-2.0, genuinely
Jetson-native — and still the wrong spend for REMY: it needs PyTorch +
transformers + a built TRT engine resident, for a capability (find/classify
arbitrary objects) that Claude's image Read already provides on demand and
that wake-on-vision doesn't require (frame-diff + moondream covers gating).

- **Stars/health:** 443, slowing (last push 2025-02) · **License:** Apache-2.0

## Marketing vs 8GB reality
- README claims "runs real-time on Jetson Orin Nano", but the performance table
  lists Orin Nano FPS as **TBD** — only AGX Orin is measured (95 FPS ViT-B/32,
  25 FPS ViT-B/16). `NVIDIA-AI-IOT/nanoowl@fb553de:README.md:L42-73`.
- Stack: PyTorch + torch2trt + TensorRT + transformers
  (`@fb553de:README.md:L78-105`). **ESTIMATE** 1.5-2.5GB+ resident with CUDA
  context — collides with REMY's 3-4GB of audio/LLM residents.

## Read these files
- `NVIDIA-AI-IOT/nanoowl@fb553de:nanoowl/owl_predictor.py:L143-172` —
  `OwlPredictor` swaps the HF vision encoder for a deserialized TRT engine.
- `@fb553de:nanoowl/owl_predictor.py:L381-455` — engine load/build via
  `trtexec --fp16`; the pattern for TRT-accelerating any ViT encoder on Jetson.

## Lift
Nothing now. If REMY ever needs a fast "is a PERSON in frame" gate smarter
than frame-diff but cheaper than a VLM, revisit this or its sibling NanoSAM —
but note the repo is coasting (one push in the last ~18 months).

## Avoid
Adopting it for the portfolio-header demo or "what am I holding" — those are
one-shot, quality-sensitive, latency-tolerant: exactly Claude-Read territory.

## License constraint
Apache-2.0 — no barrier; the barrier is RAM and maintenance.

## Jetson cost
**ESTIMATE** 1.5-2.5GB resident + engine build time; unknown Orin Nano FPS.

## Effort
**L** if ever adopted (torch stack + engine build on-device).
