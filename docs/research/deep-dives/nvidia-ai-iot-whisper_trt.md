# NVIDIA-AI-IOT/whisper_trt — VENDOR (top-priority STT answer)

Optimizes OpenAI Whisper with TensorRT via `torch2trt`. Splits Whisper into an
audio-encoder engine and a text-decoder engine, builds each as an FP16
TensorRT engine, and runs greedy autoregressive decode **on the Orin GPU**.

- **Stars/health:** 111, last push 2024-10 (stable but unmaintained) ·
  **License:** MIT (LICENSE.md + source headers are explicit SPDX MIT, despite
  the GitHub API reporting NOASSERTION)

## Does better than REMY
REMY runs faster-whisper `base` **CPU-only** because CTranslate2 has no aarch64
CUDA build (whisper_trt's own benchmark literally reports faster_whisper as
"Unavailable" on the Orin). whisper_trt is the missing GPU path.

On **Jetson Orin Nano**, 20s clip:
- `base.en`: **0.86s** (whisper_trt) vs 2.55s (PyTorch); RAM **439MB** vs 666MB.
- `tiny.en`: 0.64s vs 1.74s.

~3x faster, ~60% the RAM, and — most important on 8GB — it moves STT off the
CPU that qwen contends for.

## Read these files
- `whisper_trt@268eff1:whisper_trt/model.py:L258-277` — mel + both engines on
  `.cuda()`; `embed_audio` → `logits` → argmax loop all on GPU.
- `:L304-373` — `torch2trt.torch2trt(..., fp16_mode=True, use_onnx=True)` engine
  build with min/opt/max shapes; `:L505-522` caches to `~/.cache/whisper_trt/`.
- `:L436-466` — load prebuilt engine via `torch2trt.TRTModule`.
- `whisper_trt/vad.py:L930-1031` — a self-contained Silero-VAD ONNX wrapper
  (pinned URL+MD5 at `:L916-920`), directly usable for endpointing.
- `examples/live_transcription.py:L702-776` — multiprocess VAD→ASR pipeline
  emitting `speech_start`/`speech_end`, maps onto REMY's EventBus.

## Lift
The whole package (small, MIT) as a second STT backend behind REMY's STT
interface; keep faster-whisper as the fallback.

## Avoid
- Greedy-only decode (no beam/temperature fallback) → slightly higher WER on
  hard audio.
- Assuming it's turnkey: one-time engine build on first run; hard dep on
  torch2trt + tensorrt + PyTorch-CUDA; last push 2024-10, so **pin torch2trt
  and validate against JetPack r36 / TensorRT 10** before trusting it.

## License constraint
MIT — vendorable with attribution.

## Effort
**M** — install + one-time on-device engine build + wire `transcribe(np.ndarray)`
into the STT interface. Medium risk on r36 compatibility.
