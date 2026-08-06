# pipecat-ai/smart-turn — VENDOR

Semantic end-of-turn model. Whisper-tiny encoder + a linear classifier,
~8M params. Ships a CPU int8 build at **8MB** (GPU fp32 = 32MB). README: runs
in ~10ms on some CPUs, under 100ms on most.

- **Stars/health:** 1.5k, active (2026-01) · **License:** BSD-2-Clause (vendorable)

## Does better than REMY
REMY ends a turn on a fixed silence threshold, so it clips people mid-thought
or waits too long. smart-turn judges whether the speaker actually *finished*
("set a timer for..." vs "...for five minutes"). It reuses a Whisper encoder,
which is architecturally familiar since REMY already runs faster-whisper.

## Read these files
- `pipecat-ai/smart-turn@4786657:README.md` — architecture, size, latency (8MB
  int8 CPU, 8M params).
- The runnable weights are the HuggingFace `pipecat-ai/smart-turn-v3` ONNX — the
  same file pipecat bundles as `smart-turn-v3.2-cpu.onnx`.
- Inference wrapper (in pipecat): `pipecat@08f7aed:src/pipecat/audio/turn/smart_turn/local_smart_turn_v3.py:L26-78` loads it via
  onnxruntime with `intra_op_num_threads=cpu_count`, `inter_op=1`.

## Lift
The 8MB `smart-turn-v3.2-cpu.onnx` + the onnxruntime inference wrapper. No
PyTorch at runtime.

## Avoid
Nothing here; pair it with the state machine in the `pipecat` deep-dive rather
than reinventing the silence-gate logic.

## License constraint
BSD-2-Clause — vendorable with attribution.

## Jetson cost
~8MB model, CPU-only int8, **no GPU RAM contention**, ~10-100ms/inference on
the Orin CPU. Fits the 8GB budget trivially.

## Effort
**S** — the model file + a thin wrapper.
