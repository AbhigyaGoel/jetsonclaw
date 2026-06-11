# Custom wake words

JetsonClaw ships listening for "hey jarvis" because it is the best pretrained English wake model openWakeWord bundles. To use a different phrase you train a small model (about 200KB) and point config at it:

```toml
[wake]
model = "~/.jetsonclaw/wake/hey_remy.tflite"   # or .onnx
framework = "tflite"                            # "onnx" if you trained ONNX
threshold = 0.3
```

The prediction key is the filename stem, which the app derives automatically.

## Training options

Checked June 2026. The upstream openWakeWord training notebook is broken and unmaintained, so use one of these:

**Colab (about an hour, easiest).** The notebook linked from the [Home Assistant wake word guide](https://www.home-assistant.io/voice_control/create_wake_word/). Type your phrase, run all cells on a free T4, download both `.tflite` and `.onnx`. It is known to be flaky; dependency pins that worked recently: `tensorflow==2.19.0`, `onnx==1.17.0`, `onnxruntime==1.18.1`.

**Local with a GPU (1 to 2 hours).** [lgpearson1771/openwakeword-trainer](https://github.com/lgpearson1771/openwakeword-trainer) on Linux or WSL2 with CUDA. Needs about 15GB of disk for datasets. Exports ONNX. Two pitfalls if you use a uv-created venv: seed it with pip (`uv pip install pip setuptools wheel`) because the pipeline shells out to `python -m pip`, and use Python 3.10 or 3.11 because piper-phonemize has no 3.12 wheels.

**No training at all.** Keep the hey_jarvis model and rename the assistant in `[identity]`. The wake phrase and the assistant's name are independent.

Whatever you train, give the model adversarial negatives: phrases that sound close to your wake word ("hey jeremy", "hey memory" for "hey remy") so it learns the boundary.
