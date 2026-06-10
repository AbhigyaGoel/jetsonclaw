from pathlib import Path

from jetsonclaw.config import Config, load_config


def test_defaults_when_no_file(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("JETSONCLAW_CONFIG", str(tmp_path / "missing.toml"))
    monkeypatch.setattr("jetsonclaw.config.DEFAULT_CONFIG_PATHS", ())
    cfg = load_config()
    assert isinstance(cfg, Config)
    assert cfg.audio.sample_rate == 16000
    assert cfg.wake.model == "hey_jarvis_v0.1"


def test_partial_override(tmp_path: Path, monkeypatch):
    monkeypatch.setattr("jetsonclaw.config.DEFAULT_CONFIG_PATHS", ())
    path = tmp_path / "config.toml"
    path.write_text('[audio]\nmic_device = "plughw:1,0"\n[tts]\nenabled = false\n')
    cfg = load_config(path)
    assert cfg.audio.mic_device == "plughw:1,0"
    assert cfg.audio.sample_rate == 16000  # untouched default
    assert cfg.tts.enabled is False


def test_unknown_keys_ignored(tmp_path: Path, monkeypatch):
    monkeypatch.setattr("jetsonclaw.config.DEFAULT_CONFIG_PATHS", ())
    path = tmp_path / "config.toml"
    path.write_text('[wake]\nthreshold = 0.5\nfuture_option = "x"\n')
    cfg = load_config(path)
    assert cfg.wake.threshold == 0.5
