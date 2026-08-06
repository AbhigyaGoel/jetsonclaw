# RapidAI/RapidOCR — DEPEND (pip; OCR when Claude isn't running)

PaddleOCR's detection+recognition models exported to ONNX and served through
onnxruntime — PaddleOCR accuracy without the Paddle runtime. Pure-pip, CPU,
loads per call. This is REMY's offline/verbatim text path; Claude's Read tool
remains the default document reader when a session exists.

- **Stars/health:** 7.4k, active (2026-08) · **License:** Apache-2.0

## Does better than REMY
REMY has no OCR. RapidOCR gives deterministic, verbatim text extraction
(serials, codes, receipts, dense pages) with word boxes and confidences, fully
offline, in 1-3s on CPU — no 10-25s Claude round-trip, no session required.

## Read these files
- `RapidAI/RapidOCR@3efd66a:python/requirements.txt:L1-11` — deps:
  `numpy>=1.19.5,<3.0.0` (REMY's numpy<2 pin is inside the range),
  `opencv_python>=4.5.1.48`, pyclipper, shapely; onnxruntime installed
  separately as the engine.
- `RapidAI/RapidOCR@3efd66a:python/pyproject.toml:L1-40` — `rapidocr` package,
  py3.8-3.13, Apache-2.0, `rapidocr` CLI entry point.

## Lift
`pip install rapidocr onnxruntime` + pin `opencv-python-headless==4.11.0.86`
(cp37-abi3 manylinux aarch64 wheel; requires only `numpy>=1.21.2` on py3.10 —
verified; 4.12+/5.x wheels move to numpy>=2, do not upgrade). Wrap as a
fast-skill: `rapidocr /tmp/frame.jpg` → text to TTS. Model download ~15MB
(PP-OCRv4/v5 mobile det+rec).

## When OCR beats "let Claude read the image"
- No Claude session running / offline / latency budget <3s.
- Verbatim fidelity matters (codes, IDs, tables) — VLM transcription can
  paraphrase or drop characters.
- Anything continuous or repeated (polling a screen region).
Claude wins for: layout understanding, handwriting, "summarize this document",
mixed image+text reasoning, one-off demos where 15s is fine.

## Avoid
PaddleOCR itself (Paddle runtime on aarch64 is a build fight, ~1GB+), and the
repo's api/ocrweb/android/ios trees. Don't keep models resident — per-call
load is ~1s.

## License constraint
Apache-2.0 (models too) — clean pip DEPEND.

## Jetson cost
**ESTIMATE** ~200-400MB transient RAM per call (onnxruntime CPU), ~1-3s/image,
zero GPU, ~15MB models + ~40MB wheels disk.

## Effort
**S** — pip install + a 20-line skill.
