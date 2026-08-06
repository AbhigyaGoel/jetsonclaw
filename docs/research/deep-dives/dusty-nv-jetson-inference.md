# dusty-nv/jetson-inference — IGNORE (closed-vocab TensorRT primitives, wrong era)

Dusty's classic Hello-AI-World library: TensorRT-optimized imageNet/detectNet/
segNet/poseNet with C++/Python bindings and camera streaming. MIT (confirmed),
mature, still maintained — but its models are fixed-vocabulary (ImageNet
classes, SSD-Mobilenet COCO), which answers nothing REMY asks. "What am I
holding" needs open vocabulary; Claude's Read gives that free. Capture, its
other half, is done leaner with `v4l2-ctl` than with its GStreamer stack.

- **Stars/health:** 9.0k, active (2025-10) · **License:** MIT

## Does better than REMY
Nothing REMY needs. Its genuinely good parts — `videoSource`/`videoOutput`
abstraction (V4L2/CSI/RTP under one URI scheme) and TRT engine caching — solve
problems REMY doesn't have (one fixed USB cam, no resident vision).

## Read these files
- `dusty-nv/jetson-inference@45da40a:README.md:L4-6` — scope: TensorRT
  classification/detection/segmentation/pose primitives.
- `@45da40a:README.md:L149` — `python/examples/imagenet.py` if you ever want
  the minimal TRT-inference-loop shape on Jetson.

## Lift
None. If a closed-set detector is ever wanted (person-gate), moondream via
ollama or a ported frigate motion gate is cheaper to integrate than this
docker-first install (container is multi-GB; bare-metal build wants CMake +
TRT dev headers).

## Avoid
- Its camera path for the C720: designed around GStreamer/CSI; USB one-shots
  are two lines of `v4l2-ctl`.
- Confusing it with `jetson-containers` (the useful dusty-nv repo for REMY).

## License constraint
MIT — clean, irrelevant since nothing is taken.

## Jetson cost
n/a (not adopted); container ~multi-GB disk if it were.

## Effort
n/a.
