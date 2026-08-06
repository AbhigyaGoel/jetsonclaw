"""`python -m remy --doctor` — one command that tells a new user exactly
what's working and what to fix. Plug-and-play lives or dies on this."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import urllib.request
from pathlib import Path

from .config import Config
from .licensing import gpl_piper_installed


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
    print("\nREMY doctor\n=================")
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
                          f"download {cfg.tts.voice}.onnx and .onnx.json into "
                          f"{cfg.tts.voices_dir} (rhasspy.github.io/piper-samples)"))

    # piper binary — TTS runs it out-of-process (its GPL stays across the boundary)
    piper_bin_ok = shutil.which(cfg.tts.binary) is not None or not cfg.tts.enabled
    results.append(_check("piper binary", piper_bin_ok, cfg.tts.binary,
                          "install the piper binary; REMY execs it, never imports it"))

    # license guard — a GPL piper-tts must not be importable in-process
    gpl_reason = gpl_piper_installed()
    results.append(_check("piper license (no in-proc GPL)", gpl_reason is None,
                          gpl_reason or "clean",
                          "pip uninstall piper-tts; use the piper binary instead"))

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
                          "put it in ~/.remy/env and ~/.bashrc"))

    # BILLING FOOTGUN: if ANTHROPIC_API_KEY is set, Claude Code silently bills
    # pay-as-you-go instead of the subscription. This must be unset. Core check.
    no_api_key = not os.environ.get("ANTHROPIC_API_KEY")
    results.append(_check("no ANTHROPIC_API_KEY (subscription billing)", no_api_key,
                          "unset" if no_api_key else "SET — will bill pay-as-you-go!",
                          "unset ANTHROPIC_API_KEY everywhere (shell profile, "
                          "systemd unit, ~/.remy/env); REMY bills the subscription"))

    # agent engine — only gate on the SDK when it's actually selected
    if cfg.claude.engine == "sdk":
        try:
            import claude_agent_sdk  # noqa: F401
            sdk_ok, sdk_detail = True, "sdk"
        except Exception:
            sdk_ok, sdk_detail = False, "claude-agent-sdk not importable"
        results.append(_check("agent engine (sdk)", sdk_ok, sdk_detail,
                              "pip install claude-agent-sdk (or set [claude] engine = \"cli\")"))

    # spotify (optional)
    spotify = Path(cfg.spotify.token_file).expanduser().is_file()
    _check("spotify (optional)", spotify, "" if spotify else "not linked",
           "put OAuth tokens at " + cfg.spotify.token_file)

    # sandbox (M2 prerequisites; informational until the loader switch lands).
    # userns is the single biggest on-box unknown — see on-box-checklist.md.
    from .sandbox.detect import sandbox_report
    rep = sandbox_report()
    _check("sandbox: user namespaces", rep["userns"],
           "unprivileged userns on" if rep["userns"] else "unavailable",
           "enable unprivileged user namespaces on the L4T kernel "
           "(docs/design/on-box-checklist.md); the whole sandbox plan needs this")
    _check("sandbox: bubblewrap", rep["bwrap"],
           "bwrap" if rep["bwrap"] else "not installed",
           "sudo apt install bubblewrap socat")
    _check("sandbox: cgroup v2 memory", rep["cgroup_v2"],
           "delegated" if rep["cgroup_v2"] else "no memory controller",
           "needs cgroup v2 with a delegated memory controller for MemoryMax")

    # credential store (M4 prerequisites; informational until the broker wires in)
    from .secrets.detect import (age_available, identity_file_secure,
                                 secrets_dir_secure)
    secrets_dir = Path.home() / ".remy" / "secrets"
    _check("secrets: age binary", age_available(),
           "age" if age_available() else "not installed",
           "sudo apt install age (or rage); REMY execs it, never links it")
    _check("secrets: store perms (0700)", secrets_dir_secure(secrets_dir),
           "0700 or absent", "chmod 700 ~/.remy/secrets")
    _check("secrets: identity perms (0600)",
           identity_file_secure(secrets_dir / "identity.txt"),
           "0600 or absent", "chmod 600 ~/.remy/secrets/identity.txt")

    core_ok = all(results)
    print(f"\n{'all core checks passed — say the wake word' if core_ok else 'fix the ✗ items above, then re-run --doctor'}\n")
    return 0 if core_ok else 1
