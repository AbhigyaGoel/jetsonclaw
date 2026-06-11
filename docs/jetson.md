# Jetson notes

Setup details and pitfalls specific to the Jetson Orin Nano (JetPack r36, Ubuntu 22.04, Python 3.10). Most of these were found the hard way; they are encoded in the defaults, so you only need this page when changing things.

## Audio

- Mic capture uses `arecord` subprocesses, never PyAudio. PyAudio device indices on Jetson are unstable, break after backgrounding, and fail with channel errors.
- Find your mic with `arecord -l` and set `[audio] mic_device` (a USB mic usually lands on `plughw:2,0`).
- Audio out is HDMI only unless you add a USB speaker. Find devices with `aplay -l` and set `[audio] speaker_device`, for example `plughw:0,3` for HDMI.
- ALSA prints confmisc/dmix warnings on startup. They are cosmetic.

## Wake word

- openWakeWord must be fed int16 PCM. Float32 input silently produces near-zero scores on clear speech.
- Chunk size is 1280 samples (80ms at 16kHz), which is what the models expect.
- The bundled models are downloaded post-install by `openwakeword.utils.download_models()`; the installer does this.

## Speech to text

- The pip build of ctranslate2 has no CUDA support on aarch64, so faster-whisper runs CPU only. The `base` model with int8 quantization is real-time on the Orin Nano.
- The `tiny` model mishears uncommon words. Not worth the speedup.

## Python packaging

- numpy must stay below 2.0. tflite-runtime is compiled against numpy 1.x and crashes on 2.x. The dependency pin handles this; do not "upgrade" it.
- onnxruntime from pip is CPU only on aarch64, which is fine for both wake word and Piper.

## Memory pressure

- 8GB is shared between CPU and GPU. When ollama loads a model under cache pressure it can transiently fail with HTTP 500 (cudaMalloc out of memory). The client retries once after 2 seconds, which resolves it in practice.
- `keep_alive` is set to 24h so the chat model stays resident. First-token latency after idle would otherwise be several seconds.

## Process management

- Run in the foreground or under systemd (`scripts/jetsonclaw.service`). Backgrounding with nohup/screen has caused audio device issues.
- The systemd unit reads `~/.jetsonclaw/env` for `CLAUDE_CODE_OAUTH_TOKEN` and `PATH`.
