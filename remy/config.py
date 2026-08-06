"""Configuration loading. All tunables live in config.toml, overridable via env vars."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

try:
    import tomllib  # py311+
except ModuleNotFoundError:  # py310 (Jetson)
    import tomli as tomllib  # type: ignore[no-redef]

DEFAULT_CONFIG_PATHS = (
    Path.home() / ".remy" / "config.toml",
    Path(__file__).resolve().parent.parent / "config.toml",
)


@dataclass(frozen=True)
class IdentityConfig:
    name: str = "Remy"
    owner: str = "Chud"


@dataclass(frozen=True)
class AudioConfig:
    mic_device: str = "plughw:2,0"
    sample_rate: int = 16000
    chunk_samples: int = 1280  # 80ms at 16kHz — what openWakeWord expects
    silence_rms: float = 500.0
    silence_secs: float = 1.5
    max_record_secs: float = 10.0
    speaker_device: str = "default"


@dataclass(frozen=True)
class WakeConfig:
    model: str = "hey_jarvis_v0.1"
    framework: str = "tflite"
    threshold: float = 0.3


@dataclass(frozen=True)
class SttConfig:
    model: str = "base"
    device: str = "cpu"
    compute_type: str = "int8"
    beam_size: int = 1
    language: str = "en"


@dataclass(frozen=True)
class TtsConfig:
    enabled: bool = True
    voice: str = "en_GB-alan-medium"
    voices_dir: str = "~/.remy/voices"
    length_scale: float = 1.0
    # Piper runs out-of-process (it is GPL; REMY is MIT — never import it).
    binary: str = "piper"


@dataclass(frozen=True)
class ChatConfig:
    provider: str = "ollama"  # "ollama" or "openai" (any /v1/chat/completions endpoint)
    url: str = "http://localhost:11434/api/generate"
    model: str = "qwen2.5:3b"
    api_key_env: str = "OPENAI_API_KEY"  # env var name, openai provider only
    num_predict: int = 150
    temperature: float = 0.8
    timeout_secs: float = 30.0
    keep_alive: str = "24h"  # ollama only: keep model loaded; "-1" = forever
    # {name}/{owner} are filled from [identity] at load time
    system_prompt: str = (
        "You are {name}, a sharp personal assistant running on a Jetson. "
        "Your owner is {owner}. Keep answers to 1-3 short sentences. "
        "Be natural and helpful. No fluff."
    )



@dataclass(frozen=True)
class ClaudeConfig:
    binary: str = "claude"
    workdir: str = "~/remy"
    timeout_secs: float = 600.0
    # No Bash by default — a misheard voice command must not be able to run
    # arbitrary shell. Add ",Bash" here if you accept that tradeoff.
    # Web tools let synthesis sessions read real API docs.
    allowed_tools: str = "Read,Edit,Write,Glob,Grep,WebFetch,WebSearch"
    permission_mode: str = "acceptEdits"
    confirm_tasks: bool = True  # "say yes" gate before agent tasks run
    mcp_config: str = ""  # path to an MCP servers json; agent sessions inherit it
    heartbeat_hours: float = 0  # >0: run ~/.remy/HEARTBEAT.md as an agent task on this cadence
    # actionable requests nothing else handles escalate to the agent, which
    # solves them by growing a skill (set false for chat-only fallback)
    escalate: bool = True
    # Paths the agent must never Read, even though it holds the Read tool. Written
    # into a managed --settings file so the deny holds regardless of the workdir.
    # Containment before capability: the secrets store (M4) is denied before it
    # exists. Set () to disable (not recommended).
    deny_read: tuple[str, ...] = (
        "~/.remy/secrets/**",
        "~/.remy/env",
        "~/.remy/agent-settings.json",
        "~/spotify_tokens.json",
        "~/.claude/.credentials.json",
    )
    agent_settings_file: str = "~/.remy/agent-settings.json"


@dataclass(frozen=True)
class SpotifyConfig:
    token_file: str = "~/spotify_tokens.json"


@dataclass(frozen=True)
class ServerConfig:
    host: str = "0.0.0.0"
    port: int = 8484
    auth_token: str = ""  # if set, dashboard requires ?key=<token>


@dataclass(frozen=True)
class Config:
    identity: IdentityConfig = field(default_factory=IdentityConfig)
    # [projects] name = "path" — "edit my portfolio ..." runs the agent there
    projects: dict = field(default_factory=dict)
    audio: AudioConfig = field(default_factory=AudioConfig)
    wake: WakeConfig = field(default_factory=WakeConfig)
    stt: SttConfig = field(default_factory=SttConfig)
    tts: TtsConfig = field(default_factory=TtsConfig)
    chat: ChatConfig = field(default_factory=ChatConfig)
    claude: ClaudeConfig = field(default_factory=ClaudeConfig)
    spotify: SpotifyConfig = field(default_factory=SpotifyConfig)
    server: ServerConfig = field(default_factory=ServerConfig)


_SECTIONS = {
    "identity": IdentityConfig,
    "audio": AudioConfig,
    "wake": WakeConfig,
    "stt": SttConfig,
    "tts": TtsConfig,
    "chat": ChatConfig,
    "claude": ClaudeConfig,
    "spotify": SpotifyConfig,
    "server": ServerConfig,
}


def load_config(path: str | Path | None = None) -> Config:
    """Load config.toml, falling back to defaults for anything unspecified."""
    raw: dict = {}
    candidates = [Path(path)] if path else [Path(os.environ.get("REMY_CONFIG", ""))]
    candidates += list(DEFAULT_CONFIG_PATHS)
    for candidate in candidates:
        if candidate and candidate.is_file():
            with open(candidate, "rb") as f:
                raw = tomllib.load(f)
            break

    if "chat" not in raw and "ollama" in raw:
        raw["chat"] = raw["ollama"]  # pre-rename configs keep working

    projects = {str(k).lower(): str(v) for k, v in (raw.get("projects") or {}).items()}

    kwargs = {}
    for name, cls in _SECTIONS.items():
        section = raw.get(name, {})
        valid = {k: v for k, v in section.items() if k in cls.__dataclass_fields__}
        kwargs[name] = cls(**valid)

    identity: IdentityConfig = kwargs["identity"]
    chat: ChatConfig = kwargs["chat"]
    kwargs["chat"] = ChatConfig(**{
        **{f: getattr(chat, f) for f in chat.__dataclass_fields__},
        # plain replace, not str.format — user prompts may contain literal braces
        "system_prompt": chat.system_prompt
            .replace("{name}", identity.name)
            .replace("{owner}", identity.owner),
    })
    return Config(projects=projects, **kwargs)
