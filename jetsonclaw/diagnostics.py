"""`python -m jetsonclaw --doctor` — one command that tells a new user exactly
what's working and what to fix. Plug-and-play lives or dies on this."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import urllib.request
from pathlib import Path

from .config import Config


def _check(label: str, ok: bool, detail: str = "", fix: str = "") -> bool:
    mark = "\033[92m✓\033[0m" if ok else "\033[91m✗\033[0m"
    line = f" {mark} {label}"
    if detail:
        line += f" — {detail}"
    print(line)
    if not ok and fix:
        print(f"     fix: {fix}")
    return ok


def run_doctor(cfg: Config) -> int:
    print("\nJetsonClaw doctor\n=================")
    results = []

    # mic
    mic_ok, mic_detail = False, "arecord not found"
    if shutil.which("arecord"):
        listing = subprocess.run(["arecord", "-l"], capture_output=True,
                                 text=True).stdout
        mic_ok = "card" in listing
        mic_detail = f"device {cfg.audio.mic_device}" if mic_ok else "no capture devices"
    results.append(_check("microphone", mic_ok, mic_detail,
                          "plug in a USB mic, check `arecord -l`, set [audio] mic_device"))

    # speaker
    spk_ok = shutil.which("aplay") is not None
    results.append(_check("speaker (aplay)", spk_ok, cfg.audio.speaker_device,
                          "install alsa-utils; set [audio] speaker_device from `aplay -l`"))

    # wake model
    wake_path = Path(cfg.wake.model).expanduser()
    wake_ok = wake_path.exists() or not cfg.wake.model.endswith((".tflite", ".onnx"))
    results.append(_check("wake word model", wake_ok, cfg.wake.model,
                          "file missing — retrain or fix [wake] model path"))

    # piper voice
    voice = Path(cfg.tts.voices_dir).expanduser() / f"{cfg.tts.voice}.onnx"
    results.append(_check("piper voice", voice.is_file() or not cfg.tts.enabled,
                          cfg.tts.voice,
                          f"python3 -m piper.download_voices {cfg.tts.voice} "
                          f"--data-dir {cfg.tts.voices_dir}"))

    # chat brain
    if cfg.chat.provider == "ollama":
        chat_ok, chat_detail = False, "unreachable"
        try:
            base = cfg.chat.url.rsplit("/api/", 1)[0]
            with urllib.request.urlopen(f"{base}/api/tags", timeout=5) as resp:
                models = [m["name"] for m in json.loads(resp.read()).get("models", [])]
            chat_ok = cfg.chat.model in models
            chat_detail = cfg.chat.model if chat_ok else \
                f"{cfg.chat.model} not pulled (have: {', '.join(models[:3]) or 'none'})"
        except Exception as e:
            chat_detail = str(e)[:60]
        results.append(_check("chat brain (ollama)", chat_ok, chat_detail,
                              f"curl -fsSL https://ollama.com/install.sh | sh && "
                              f"ollama pull {cfg.chat.model}"))
    else:
        key_ok = bool(os.environ.get(cfg.chat.api_key_env))
        results.append(_check(f"chat brain ({cfg.chat.provider})", key_ok,
                              f"{cfg.chat.model} via {cfg.chat.url}",
                              f"set {cfg.chat.api_key_env} in the environment"))

    # claude
    claude_ok = shutil.which(cfg.claude.binary) is not None
    token_ok = bool(os.environ.get("CLAUDE_CODE_OAUTH_TOKEN")) or \
        (Path.home() / ".claude" / ".credentials.json").exists()
    results.append(_check("claude CLI", claude_ok, "",
                          "curl -fsSL https://claude.ai/install.sh | bash"))
    results.append(_check("claude auth", token_ok,
                          "" if token_ok else "no token in environment",
                          "run `claude setup-token` on a machine with a browser, "
                          "put it in ~/.jetsonclaw/env and ~/.bashrc"))

    # spotify (optional)
    spotify = Path(cfg.spotify.token_file).expanduser().is_file()
    _check("spotify (optional)", spotify, "" if spotify else "not linked",
           "put OAuth tokens at " + cfg.spotify.token_file)

    core_ok = all(results)
    print(f"\n{'all core checks passed — say the wake word' if core_ok else 'fix the ✗ items above, then re-run --doctor'}\n")
    return 0 if core_ok else 1
