import json

from remy.audio.tts import DEFAULT_SAMPLE_RATE, piper_cmd, read_sample_rate


def test_piper_cmd_is_argv_no_shell():
    cmd = piper_cmd("piper", "/voices/alan.onnx", 1.0)
    assert cmd[0] == "piper"
    assert "--model" in cmd
    assert cmd[cmd.index("--model") + 1] == "/voices/alan.onnx"
    assert "--output-raw" in cmd  # stream raw PCM to stdout
    assert cmd[cmd.index("--length-scale") + 1] == "1.0"


def test_read_sample_rate_from_companion_json(tmp_path):
    model = tmp_path / "voice.onnx"
    model.write_bytes(b"")
    (tmp_path / "voice.onnx.json").write_text(json.dumps({"audio": {"sample_rate": 16000}}))
    assert read_sample_rate(model) == 16000


def test_read_sample_rate_defaults_when_missing(tmp_path):
    assert read_sample_rate(tmp_path / "nope.onnx") == DEFAULT_SAMPLE_RATE


def test_read_sample_rate_defaults_on_malformed_json(tmp_path):
    model = tmp_path / "voice.onnx"
    (tmp_path / "voice.onnx.json").write_text("{not json")
    assert read_sample_rate(model) == DEFAULT_SAMPLE_RATE
