# k2-fsa/sherpa-onnx — DEPEND

An ONNX-Runtime C++/C/Python engine for streaming & non-streaming ASR
(Zipformer/Paraformer transducers), keyword spotting, and Silero VAD. README
lists **Jetson Orin NX and Jetson Nano as officially supported, CPU and GPU**.

- **Stars/health:** 14.0k, active (2026-08) · **License:** Apache-2.0
  (vendorable; per-model weights vary)

## Does better than REMY
Gives **partial/streaming transcripts** (REMY's faster-whisper is
utterance-complete only) AND an on-device **keyword-spotting** wake path — it
could unify wake + STT in one ONNX runtime, and its Zipformer transducer streams
natively without Whisper's 30s window.

## Read these files
- `k2-fsa/sherpa-onnx@00ad9a1:README.md:L70-106` — the capabilities matrix (ASR
  streaming, VAD, KWS; platforms incl. Jetson; C/C++/Python/Go/C#); `:L91-92`
  Jetson Orin NX + Nano supported; `:L32` aarch64.

## Lift
Adopt as an optional streaming STT backend (prebuilt aarch64 wheels exist).

## Avoid
A rip-and-replace: Zipformer WER differs from Whisper base; it's a large C++ dep;
GPU on Jetson is via onnxruntime (not TensorRT), so the speedup is smaller than
whisper_trt's.

## License constraint
Apache-2.0 — vendorable with attribution.

## Jetson cost
Streaming Zipformer ~100-300MB depending on model; onnxruntime; Jetson CPU/GPU.

## Effort
**M-L.**
