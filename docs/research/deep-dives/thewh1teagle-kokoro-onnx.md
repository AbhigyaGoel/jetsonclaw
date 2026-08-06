# thewh1teagle/kokoro-onnx (+ hexgrad/kokoro) — DEPEND (the only realistic neural TTS upgrade)

Kokoro-82M is an 82M-param open-weight TTS. `hexgrad/kokoro` is the PyTorch
reference (Apache-2.0); `thewh1teagle/kokoro-onnx` is the MIT ONNX wrapper that
runs it on CPU via onnxruntime with no torch/transformers at inference.

- **Stars/health:** kokoro-onnx 2.7k active (2026-07); kokoro 8.3k (2025-08) ·
  **License:** kokoro-onnx MIT + kokoro weights Apache-2.0 — the cleanest
  dual-permissive license of any neural TTS in the scan

## Does better than REMY
Noticeably more natural/expressive prosody than Piper VITS at a still-small
size, multiple voices/accents including British-style options. The one candidate
that could clear the "clearly better quality" bar for replacing/augmenting Piper.

## Read these files
- `thewh1teagle/kokoro-onnx@98ea02:README.md` — license (MIT wrapper + Apache-2.0
  model) + CPU/GPU support + "near real-time on macOS M1."
- `hexgrad/kokoro@dfb907:pyproject.toml` — deps `misaki[en]`, `numpy`, `torch`,
  `transformers` (the torch+transformers footprint is the RAM problem — use the
  ONNX path to avoid loading them). `LICENSE:L1-3` — Apache-2.0 code.

## Orin Nano reality
ONNX model ~300MB on disk; CPU RSS ~0.5-1GB during synthesis. On M1 it's near
real-time; on the Orin's slower ARM CPU expect **RTF ~1-2x (borderline)** —
acceptable only with sentence-by-sentence streaming (which REMY already does for
Piper). Does **not** need the GPU (essential, since whisper+qwen own it). Uses
`espeak-ng` (same dep family as Piper). No voice cloning.

## Lift
The `kokoro-onnx` CPU path as an *optional alternate voice*; keep Piper default.

## Avoid
The full `hexgrad/kokoro` torch stack. **Gate adoption on a real Orin RTF
benchmark** — it's borderline in the 8GB budget.

## License constraint
MIT wrapper + Apache-2.0 weights — fully clear for MIT REMY.

## Effort
**M** — wire an alternate TTS backend behind the existing streaming interface;
validate RTF/RAM on hardware before committing.
