# Master Index

Every repo fetched and verified during the scan, deduped across clusters,
sorted by verdict then relevance. Metadata captured 2026-08-05 via `gh api`.
Repos scoring relevance >= 3 (and worth the depth) have a note in
`deep-dives/`. Scores are 0-5.

Verdicts: **VENDOR** copy code w/ attribution · **PORT** reimplement the
pattern · **DEPEND** add as a dependency · **PATTERN-ONLY** ideas only, license
or weight forbids vendoring · **IGNORE** (reason inline).

## VENDOR — permissive license, copy the code

| Repo | Stars | Last | License | Area | Rel | Lift | Health | Verdict |
|---|---|---|---|---|---|---|---|---|
| [pipecat-ai/smart-turn](https://github.com/pipecat-ai/smart-turn) | 1.5k | 2026-01 | BSD-2 | semantic end-of-turn (8MB CPU ONNX) | 5 | 5 | 4 | VENDOR |
| [NVIDIA-AI-IOT/whisper_trt](https://github.com/NVIDIA-AI-IOT/whisper_trt) | 111 | 2024-10 | MIT | Jetson TensorRT Whisper (GPU) | 5 | 4 | 3 | VENDOR |
| [rhasspy/wyoming](https://github.com/rhasspy/wyoming) | 383 | 2026-07 | MIT | JSONL event protocol + stage enum | 5 | 5 | 5 | VENDOR |
| [Aider-AI/aider](https://github.com/Aider-AI/aider) | 48.0k | 2026-05 | Apache-2.0 | repo-map (tree-sitter + PageRank) | 5 | 4 | 5 | VENDOR |
| [mem0ai/mem0](https://github.com/mem0ai/mem0) | 62.6k | 2026-08 | Apache-2.0 | extract+reconcile memory prompts | 5 | 4 | 5 | VENDOR |
| [dnhkng/GlaDOS](https://github.com/dnhkng/GlaDOS) | 5.7k | 2026-08 | MIT | end-to-end loop + barge-in | 5 | 4 | 5 | VENDOR |
| [librespot-org/librespot](https://github.com/librespot-org/librespot) | 6.9k | 2026-07 | MIT | Spotify w/o Web API (Rust lib) | 4 | 3 | 4 | VENDOR |
| [ILikeAI/AlwaysReddy](https://github.com/ILikeAI/AlwaysReddy) | 757 | 2025-03 | MIT | Piper streaming wrapper (archived) | 3 | 4 | 2 | VENDOR |

## PORT — reimplement the pattern ourselves

| Repo | Stars | Last | License | Area | Rel | Lift | Health | Verdict |
|---|---|---|---|---|---|---|---|---|
| [OpenVoiceOS/ovos-core](https://github.com/OpenVoiceOS/ovos-core) | 283 | 2026-08 | Apache-2.0 | confidence-tiered intent router | 5 | 4 | 5 | PORT |
| [pipecat-ai/pipecat](https://github.com/pipecat-ai/pipecat) | 14.0k | 2026-08 | BSD-2 | turn state machine + barge-in guard | 5 | 4 | 5 | PORT |
| [livekit/agents](https://github.com/livekit/agents) | 12.7k | 2026-08 | Apache-2.0 | text-based end-of-turn model | 5 | 4 | 5 | PORT |
| [KoljaB/RealtimeSTT](https://github.com/KoljaB/RealtimeSTT) | 10.0k | 2026-06 | MIT | streaming STT + dual VAD | 5 | 4 | 5 | PORT |
| [MineDojo/Voyager](https://github.com/MineDojo/Voyager) | 7.1k | 2024-04 | MIT | skill library + self-verify loop | 5 | 4 | 3 | PORT |
| [jennyzzt/dgm](https://github.com/jennyzzt/dgm) | 2.2k | 2025-08 | Apache-2.0 | self-edit w/ validation gate + archive | 5 | 4 | 4 | PORT |
| [letta-ai/letta](https://github.com/letta-ai/letta) | 24.1k | 2026-08 | Apache-2.0 | MemGPT self-editing memory tiers | 5 | 4 | 5 | PORT |
| [anthropics/skills](https://github.com/anthropics/skills) | 166k | 2026-07 | Apache-2.0 | Agent Skills SKILL.md spec | 5 | 5 | 5 | PORT |
| [OpenVoiceOS/ovos-workshop](https://github.com/OpenVoiceOS/ovos-workshop) | 6 | 2026-08 | Apache-2.0 | skill loader + clean hot-reload | 5 | 3 | 4 | PORT |
| [rhasspy/wyoming-faster-whisper](https://github.com/rhasspy/wyoming-faster-whisper) | 360 | 2026-07 | MIT | faster-whisper CPU + silero pre-clip | 5 | 5 | 4 | PORT |
| [SWE-agent/SWE-agent](https://github.com/SWE-agent/SWE-agent) | 20.0k | 2026-08 | MIT | patch-as-artifact + promising gate | 4 | 3 | 5 | PORT |
| [MaximeRobeyns/self_improving_coding_agent](https://github.com/MaximeRobeyns/self_improving_coding_agent) | 378 | 2025-04 | MIT | live overseer/watchdog | 4 | 3 | 3 | PORT |
| [pytest-dev/pluggy](https://github.com/pytest-dev/pluggy) | 1.7k | 2026-08 | MIT | hookspec loader + is_blocked quarantine | 4 | 4 | 5 | PORT |
| [caspianmoon/memoripy](https://github.com/caspianmoon/memoripy) | 693 | 2026-03 | Apache-2.0 | memory decay/reinforcement | 4 | 3 | 3 | PORT |
| [memodb-io/memobase](https://github.com/memodb-io/memobase) | 2.8k | 2026-01 | Apache-2.0 | profile + event timeline (no vectors) | 4 | 3 | 4 | PORT |
| [ufal/whisper_streaming](https://github.com/ufal/whisper_streaming) | 3.7k | 2025-11 | MIT | LocalAgreement streaming policy | 3 | 4 | 3 | PORT |
| [ufal/SimulStreaming](https://github.com/ufal/SimulStreaming) | 651 | 2026-07 | MIT | AlignAtt streaming policy (successor) | 3 | 3 | 4 | PORT |
| [codelion/openevolve](https://github.com/codelion/openevolve) | 6.9k | 2026-07 | Apache-2.0 | cascade evaluation ordering | 3 | 3 | 5 | PORT |
| [leon-ai/leon](https://github.com/leon-ai/leon) | 17.4k | 2026-08 | MIT | structured skill manifest + locales | 4 | 3 | 5 | PORT |
| [PromtEngineer/Verbi](https://github.com/PromtEngineer/Verbi) | 1.1k | 2025-11 | MIT | modular STT/LLM/TTS provider iface | 3 | 3 | 4 | PORT |

## DEPEND — add as a dependency (Jetson cost recorded in deep-dive)

| Repo | Stars | Last | License | Area | Rel | Lift | Health | Verdict |
|---|---|---|---|---|---|---|---|---|
| [snakers4/silero-vad](https://github.com/snakers4/silero-vad) | 9.9k | 2026-07 | MIT | VAD, ~2MB ONNX, <1ms/chunk | 5 | 5 | 5 | DEPEND |
| [dusty-nv/jetson-containers](https://github.com/dusty-nv/jetson-containers) | 4.8k | 2026-08 | Apache-2.0* | prebuilt r36 arm64 model images | 5 | 5 | 5 | DEPEND |
| [devgianlu/go-librespot](https://github.com/devgianlu/go-librespot) | 345 | 2026-08 | GPL-3.0 | Spotify sidecar, REST+WS, no app reg | 5 | 3 | 5 | DEPEND |
| [containers/bubblewrap](https://github.com/containers/bubblewrap) | 8.3k | 2026-06 | LGPL-2.0+ | unprivileged sandbox (wrap binary) | 5 | 4 | 5 | DEPEND |
| [anthropics/claude-agent-sdk-python](https://github.com/anthropics/claude-agent-sdk-python) | 7.8k | 2026-08 | MIT | headless CC + can_use_tool gate | 5 | 5 | 5 | DEPEND |
| [dscripka/openWakeWord](https://github.com/dscripka/openWakeWord) | 2.6k | 2025-12 | Apache-2.0 | wake word (in use; tuning levers) | 5 | 5 | 5 | DEPEND |
| [rhasspy/piper](https://github.com/rhasspy/piper) | 11.3k | 2025-08 | MIT | TTS (in use; pin MIT release) | 5 | 5 | 2 | DEPEND |
| [SYSTRAN/faster-whisper](https://github.com/SYSTRAN/faster-whisper) | 24.8k | 2025-11 | MIT | STT (in use; CPU config) | 4 | 5 | 5 | DEPEND |
| [Anthropic memory tool + context editing](https://platform.claude.com/docs/en/agents-and-tools/tool-use/memory-tool) | n/a | 2026-08 | vendor docs | file-based agent memory | 5 | 5 | 5 | DEPEND |
| [k2-fsa/sherpa-onnx](https://github.com/k2-fsa/sherpa-onnx) | 14.0k | 2026-08 | Apache-2.0 | streaming ASR/KWS/VAD runtime, Jetson | 4 | 3 | 5 | DEPEND |
| [usefulsensors/moonshine](https://github.com/usefulsensors/moonshine) | 10.6k | 2026-08 | MIT (EN) | streaming edge STT (arm64) | 4 | 3 | 5 | DEPEND |
| [thewh1teagle/kokoro-onnx](https://github.com/thewh1teagle/kokoro-onnx) | 2.7k | 2026-07 | MIT | Kokoro TTS CPU runtime | 4 | 4 | 4 | DEPEND |
| [Textualize/textual](https://github.com/Textualize/textual) | 36.9k | 2026-07 | MIT | TUI + `textual serve` browser | 4 | 5 | 5 | DEPEND |
| [hexgrad/kokoro](https://github.com/hexgrad/kokoro) | 8.3k | 2025-08 | Apache-2.0 | neural TTS weights (via ONNX) | 4 | 3 | 4 | DEPEND |
| [spotipy-dev/spotipy](https://github.com/spotipy-dev/spotipy) | 5.5k | 2026-06 | MIT | Spotify Web API (current path) | 3 | 4 | 5 | DEPEND |
| [ggml-org/whisper.cpp](https://github.com/ggml-org/whisper.cpp) | 52.6k | 2026-08 | MIT | STT, CUDA build on Orin | 3 | 3 | 5 | DEPEND |

## PATTERN-ONLY — read for ideas; license/weights forbid vendoring

| Repo | Stars | Last | License | Area | Rel | Lift | Health | Verdict |
|---|---|---|---|---|---|---|---|---|
| [home-assistant/core](https://github.com/home-assistant/core) (assist_pipeline) | 89.8k | 2026-08 | Apache-2.0 | pipeline event taxonomy + VAD sensitivity | 5 | 3 | 5 | PATTERN-ONLY |
| [OHF-Voice/piper1-gpl](https://github.com/OHF-Voice/piper1-gpl) | 5.0k | 2026-08 | GPL-3.0 | maintained Piper (subprocess-only) | 4 | 2 | 5 | PATTERN-ONLY |
| [KoljaB/RealtimeVoiceChat](https://github.com/KoljaB/RealtimeVoiceChat) | 3.8k | 2025-07 | none | dynamic pause turn-taking | 4 | 2 | 4 | PATTERN-ONLY |
| [KoljaB/RealtimeTTS](https://github.com/KoljaB/RealtimeTTS) | 4.0k | 2026-08 | MIT | thread-safe TTS stop | 4 | 4 | 5 | PATTERN-ONLY |
| [acon96/home-llm](https://github.com/acon96/home-llm) | 1.4k | 2026-07 | custom | small-model function-call prompt | 4 | 3 | 5 | PATTERN-ONLY |
| [google/nsjail](https://github.com/google/nsjail) | 4.0k | 2026-07 | Apache-2.0 | sandbox w/ cgroup caps (heavier) | 4 | 3 | 5 | PATTERN-ONLY |
| [rhasspy/wyoming-satellite](https://github.com/rhasspy/wyoming-satellite) | 1.2k | 2026-01 | MIT | satellite/server split (archived) | 4 | 4 | 3 | PATTERN-ONLY |
| [TEN-framework/TEN-Agent](https://github.com/TEN-framework/TEN-Agent) | 11.0k | 2026-08 | NOASSERTION | full-duplex + AEC node graph | 3 | 2 | 5 | PATTERN-ONLY |
| [alphacep/vosk-api](https://github.com/alphacep/vosk-api) | 15.0k | 2026-07 | Apache-2.0 | streaming Kaldi ASR | 3 | 3 | 5 | PATTERN-ONLY |
| [All-Hands-AI/OpenHands](https://github.com/All-Hands-AI/OpenHands) | 83.2k | 2026-08 | MIT | Docker-isolated agent runtime | 3 | 2 | 5 | PATTERN-ONLY |
| [BasedHardware/omi](https://github.com/BasedHardware/omi) | 13.1k | 2026-08 | MIT | always-on capture + consolidation | 3 | 1 | 5 | PATTERN-ONLY |
| [huggingface/speech-to-speech](https://github.com/huggingface/speech-to-speech) | 11.2k | 2026-08 | Apache-2.0 | modular S2S blocks (GPU) | 3 | 2 | 5 | PATTERN-ONLY |
| [KoljaB/Linguflex](https://github.com/KoljaB/Linguflex) | 812 | 2025-06 | none | full assistant + skills | 3 | 2 | 3 | PATTERN-ONLY |
| [mezbaul-h/june](https://github.com/mezbaul-h/june) | 788 | 2024-08 | MIT | Ollama+Whisper+Coqui loop (stale) | 3 | 3 | 2 | PATTERN-ONLY |
| [topoteretes/cognee](https://github.com/topoteretes/cognee) | 29.8k | 2026-08 | Apache-2.0 | KG memory + Claude Code plugin | 3 | 2 | 5 | PATTERN-ONLY |
| [collabora/WhisperLive](https://github.com/collabora/WhisperLive) | 4.2k | 2026-08 | MIT | streaming STT server (heavy backend) | 3 | 2 | 5 | PATTERN-ONLY |
| [myshell-ai/MeloTTS](https://github.com/myshell-ai/MeloTTS) | 7.6k | 2024-12 | MIT | CPU real-time TTS (no British voice) | 3 | 2 | 3 | PATTERN-ONLY |
| [khoj-ai/khoj](https://github.com/khoj-ai/khoj) | 36.3k | 2026-08 | AGPL-3.0 | multi-surface assistant design | 3 | 1 | 5 | PATTERN-ONLY |
| [open-webui/open-webui](https://github.com/open-webui/open-webui) | 148k | 2026-08 | NOASSERTION | PWA + voice UX | 3 | 2 | 5 | PATTERN-ONLY |
| [NVIDIA-AI-IOT/jetson-copilot](https://github.com/NVIDIA-AI-IOT/jetson-copilot) | 127 | 2024-12 | Apache-2.0 | Ollama+RAG on Orin reference | 3 | 3 | 2 | PATTERN-ONLY |
| [dusty-nv/NanoLLM](https://github.com/dusty-nv/NanoLLM) | 382 | 2024-10 | MIT | Jetson ASR->LLM->TTS pipeline | 3 | 2 | 2 | PATTERN-ONLY |
| [Spotifyd/spotifyd](https://github.com/Spotifyd/spotifyd) | 10.7k | 2026-05 | GPL-3.0 | Spotify Connect daemon (MPRIS) | 3 | 2 | 5 | PATTERN-ONLY |
| [musistudio/claude-code-router](https://github.com/musistudio/claude-code-router) | 36.4k | 2026-08 | MIT | CC control plane / cred pool | 3 | 2 | 5 | PATTERN-ONLY |
| [sst/opencode](https://github.com/sst/opencode) | 194k | 2026-08 | MIT | alt permission-gating harness | 3 | 2 | 5 | PATTERN-ONLY |
| [MycroftAI/mycroft-core](https://github.com/MycroftAI/mycroft-core) | 6.6k | 2024-09 | Apache-2.0 | original skill API (archived) | 3 | 2 | 1 | PATTERN-ONLY |
| [toverainc/willow-inference-server](https://github.com/toverainc/willow-inference-server) | 510 | 2026-02 | Apache-2.0 | GPU ASR/TTS server | 3 | 1 | 3 | PATTERN-ONLY |
| [rhasspy/rhasspy3](https://github.com/rhasspy/rhasspy3) | 382 | 2023-12 | MIT | pipeline-of-programs (archived) | 3 | 2 | 1 | PATTERN-ONLY |
| [idiap/coqui-ai-TTS](https://github.com/idiap/coqui-ai-TTS) | 2.3k | 2026-06 | MPL-2.0 / CPML | XTTS cloning (non-commercial weights) | 2 | 1 | 4 | PATTERN-ONLY |
| [SWivid/F5-TTS](https://github.com/SWivid/F5-TTS) | 15.1k | 2026-07 | MIT / CC-BY-NC | flow-match cloning (NC weights, GPU) | 2 | 1 | 5 | PATTERN-ONLY |
| [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers) | 89.3k | 2026-08 | MIT | MCP as alt skill transport | 2 | 2 | 5 | PATTERN-ONLY |
| [Significant-Gravitas/AutoGPT](https://github.com/Significant-Gravitas/AutoGPT) | 186k | 2026-08 | Polyform-Shield | failure-mode case study | 2 | 0 | 5 | PATTERN-ONLY |
| [kahrendt/microWakeWord](https://github.com/kahrendt/microWakeWord) | 3 | 2026-07 | Apache-2.0 | wake word (ESP32/MCU) | 2 | 1 | 3 | PATTERN-ONLY |
| [Picovoice/porcupine](https://github.com/Picovoice/porcupine) | 4.9k | 2026-08 | Apache-2.0 (SDK) | wake word eval methodology only | 1 | 0 | 5 | PATTERN-ONLY |
| [kalliope-project/kalliope](https://github.com/kalliope-project/kalliope) | 1.8k | 2023-07 | GPL-3.0 | YAML synapse engine | 2 | 1 | 1 | PATTERN-ONLY |

## IGNORE

| Repo | Stars | Last | License | Reason |
|---|---|---|---|---|
| [Significant-Gravitas/AutoGPT] see above | | | | (kept as PATTERN-ONLY case study) |
| [SakanaAI/self-adaptive-llms](https://github.com/SakanaAI/self-adaptive-llms) | 1.2k | 2025-01 | Apache-2.0 | weight-space adaptation, not code self-mod |
| [gpt-engineer-org/gpt-engineer](https://github.com/gpt-engineer-org/gpt-engineer) | 55.2k | 2025-05 | MIT | archived, one-shot codegen, no self-mod |
| [getzep/zep](https://github.com/getzep/zep) | 4.8k | 2026-08 | Apache-2.0 | Graphiti KG + Neo4j + embeddings, too heavy for 8GB |
| [kingjulio8238/Memary](https://github.com/kingjulio8238/Memary) | 2.6k | 2024-10 | MIT | stale 22mo, KG-heavy, needs Neo4j+embeddings |
| [OpenInterpreter/01](https://github.com/OpenInterpreter/01) | 5.1k | 2024-11 | AGPL-3.0 | AGPL + stale; copyleft blocks vendoring |
| [OpenInterpreter/open-interpreter](https://github.com/OpenInterpreter/open-interpreter) | 67.7k | 2026-08 | Apache-2.0 | code-executing agent, not a voice loop |
| [toverainc/willow](https://github.com/toverainc/willow) | 3.1k | 2026-08 | Apache-2.0 | ESP32 firmware satellite, no Jetson lift |
| [NeonGeckoCom/NeonCore](https://github.com/NeonGeckoCom/NeonCore) | 210 | 2026-08 | BSD-3 | OVOS fork; OVOS is the better source |
| [vocodedev/vocode-core](https://github.com/vocodedev/vocode-core) | 3.8k | 2024-11 | MIT | stale 18mo+; pipecat/livekit are alive |
| [NVIDIA/NeMo](https://github.com/NVIDIA/NeMo) | 17.9k | 2026-08 | Apache-2.0 | parakeet accurate but framework too heavy for 8GB |
| [MycroftAI/mycroft-precise](https://github.com/MycroftAI/mycroft-precise) | 962 | 2023-11 | Apache-2.0 | dead 2.5yr, openWakeWord supersedes |
| [coqui-ai/TTS](https://github.com/coqui-ai/TTS) | 45.9k | 2024-08 | MPL-2.0 / CPML | dead upstream, XTTS weights non-commercial |
| [yl4579/StyleTTS2](https://github.com/yl4579/StyleTTS2) | 6.3k | 2024-08 | MIT | research repo, GPU-bound, 12mo+ stale |
| [canopyai/Orpheus-TTS](https://github.com/canopyai/Orpheus-TTS) | 6.3k | 2025-12 | Apache-2.0 | 3B Llama TTS, won't fit alongside qwen |
| [microsandbox/microsandbox](https://github.com/microsandbox/microsandbox) | 7.1k | 2026-08 | Apache-2.0 | needs KVM/libkrun, not on Jetson |
| [e2b-dev/E2B](https://github.com/e2b-dev/E2B) | 13.3k | 2026-08 | Apache-2.0 | cloud/Firecracker, not on-device |
| [danny-avila/LibreChat](https://github.com/danny-avila/LibreChat) | 41.7k | 2026-08 | MIT | too heavy for the device's role |
| [dusty-nv/jetson-inference](https://github.com/dusty-nv/jetson-inference) | 9.0k | 2025-10 | MIT | vision-focused, not voice |
| [vndee/local-talking-llm](https://github.com/vndee/local-talking-llm) | 882 | 2026-04 | MIT | tutorial-grade |
| [punkpeye/awesome-mcp-servers](https://github.com/punkpeye/awesome-mcp-servers) | 91.9k | 2026-08 | MIT | index list, no code |
| [hesreallyhim/awesome-claude-code](https://github.com/hesreallyhim/awesome-claude-code) | 51.7k | 2026-08 | NOASSERTION | index list, no code |
| [TEN-framework/ten-vad](https://github.com/TEN-framework/ten-vad) | 2.2k | 2026-02 | NOASSERTION | silero-vad is the licensed choice |

\*jetson-containers: repo header NOASSERTION; per-package licenses are mostly Apache-2.0/MIT — verify per file before vendoring. whisper_trt: header reads NOASSERTION but LICENSE.md + source headers are explicit MIT.

## Blind-spot additions (captured 2026-08-06)

Second pass covering areas the voice-seeded scan missed: MCP, browser control,
vision, job orchestration, secrets/OAuth, containment. Analysis in
`blindspots.md`.

### DEPEND

| Repo | Stars | Last | License | Area | Rel | Verdict |
|---|---|---|---|---|---|---|
| [anthropics/claude-agent-sdk-python](https://github.com/anthropics/claude-agent-sdk-python) | 7.8k | 2026-08 | MIT | job engine: resume-by-ID, can_use_tool, hooks, in-process MCP (deep-dive rewritten) | 5 | DEPEND |
| [containers/bubblewrap](https://github.com/containers/bubblewrap) | 8.3k | 2026-06 | LGPL-2.0+ | primary sandbox; concrete A/B/C profiles (deep-dive rewritten) | 5 | DEPEND |
| [anthropic-experimental/sandbox-runtime](https://github.com/anthropic-experimental/sandbox-runtime) | 4.9k | 2026-08 | Apache-2.0 | Claude Code's own Bash sandbox (bwrap+proxy), arm64 | 5 | DEPEND |
| [microsoft/playwright-mcp](https://github.com/microsoft/playwright-mcp) | 36k | 2026-08 | Apache-2.0 | the single browser capability via --mcp-config | 5 | DEPEND |
| [microsoft/playwright](https://github.com/microsoft/playwright) | 94k | 2026-08 | Apache-2.0 | official ubuntu22.04-arm64 headless-shell builds | 5 | DEPEND |
| [taylorwilsdon/google_workspace_mcp](https://github.com/taylorwilsdon/google_workspace_mcp) | 3.0k | 2026-08 | MIT | Gmail+Calendar+Drive, LAN-configurable OAuth callback; only healthy Gmail path | 5 | DEPEND |
| [github/github-mcp-server](https://github.com/github/github-mcp-server) | 32k | 2026-08 | MIT | official, prebuilt linux-arm64, PAT/device-code | 5 | DEPEND |
| [modelcontextprotocol/python-sdk](https://github.com/modelcontextprotocol/python-sdk) | 24k | 2026-08 | MIT | REMY's own tools as a stdio MCP server | 5 | DEPEND |
| [cli/cli](https://github.com/cli/cli) | 46k | 2026-08 | MIT | gh device flow + token storage solves GitHub auth | 4 | DEPEND |
| [FiloSottile/age](https://github.com/FiloSottile/age) | 23k | 2026-03 | BSD-3 | at-rest encryption for ~/.remy/secrets | 4 | DEPEND |
| [yt-dlp/yt-dlp](https://github.com/yt-dlp/yt-dlp) | 182.7k | 2026-08 | Unlicense | TikTok/media metadata batch fetch | 4 | DEPEND |
| [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers) | 89k | 2026-08 | MIT | filesystem reference server (upgraded from PATTERN-ONLY) | 4 | DEPEND |
| [vikhyat/moondream](https://github.com/vikhyat/moondream) | 9.9k | 2026-04 | Apache-2.0 | the one local VLM if ever needed (ollama, transient) | 3 | DEPEND |
| [RapidAI/RapidOCR](https://github.com/RapidAI/RapidOCR) | 7.4k | 2026-08 | Apache-2.0 | offline OCR, numpy<2 safe | 3 | DEPEND |
| [opencv/opencv-python](https://github.com/opencv/opencv-python) | 5.3k | 2026-07 | MIT | pin headless==4.11.0.86 (numpy<2 tripwire) | 3 | DEPEND |
| [tesseract-ocr/tesseract](https://github.com/tesseract-ocr/tesseract) | 75.8k | 2026-08 | Apache-2.0 | apt OCR fallback | 2 | DEPEND |
| [nspady/google-calendar-mcp](https://github.com/nspady/google-calendar-mcp) | 1.2k | 2026-06 | MIT | calendar-only fallback server | 2 | DEPEND |
| [Zouuup/landrun](https://github.com/Zouuup/landrun) | 2.3k | 2026-07 | MIT | Landlock CLI, conditional on L4T kernel config | 2 | DEPEND |

### PATTERN-ONLY

| Repo | Stars | Last | License | Area | Rel | Verdict |
|---|---|---|---|---|---|---|
| [rclone/rclone](https://github.com/rclone/rclone) | 59k | 2026-08 | MIT | `rclone authorize` headless-OAuth relay pattern | 4 | PATTERN-ONLY |
| [99designs/aws-vault](https://github.com/99designs/aws-vault) | 9k | 2025-12 | MIT | credential-broker shape: child gets URL+bearer, never the secret | 4 | PATTERN-ONLY |
| [OpenHands/software-agent-sdk](https://github.com/OpenHands/software-agent-sdk) | 961 | 2026-08 | MIT | events.jsonl per job, TTL lease, cancellation token | 4 | PATTERN-ONLY |
| [litements/litequeue](https://github.com/litements/litequeue) | 231 | 2026-07 | MIT | sqlite claim/CAS + retry_expired idioms | 3 | PATTERN-ONLY |
| [peter-wangxu/persist-queue](https://github.com/peter-wangxu/persist-queue) | 390 | 2026-01 | BSD-3 | boot-sweep of unacked tasks (pid-gate it) | 3 | PATTERN-ONLY |
| [browser-use/browser-use](https://github.com/browser-use/browser-use) | 108k | 2026-08 | MIT | prompts only; API-key loop + py3.11 block adoption | 3 | PATTERN-ONLY |
| [blakeblackshear/frigate](https://github.com/blakeblackshear/frigate) | 34.9k | 2026-08 | MIT | ~80-line motion gate for wake-on-vision | 3 | PATTERN-ONLY |
| [NVIDIA-AI-IOT/live-vlm-webui](https://github.com/NVIDIA-AI-IOT/live-vlm-webui) | 415 | 2026-03 | Apache-2.0 | webcam-to-VLM loop shape | 2 | PATTERN-ONLY |

### IGNORE

| Repo | License | Reason |
|---|---|---|
| [coleifer/huey](https://github.com/coleifer/huey) | MIT | dequeue deletes the row before the task runs — no crash recovery |
| [agronholm/apscheduler](https://github.com/agronholm/apscheduler) | MIT | persists schedules, not running-job state; 4.x still alpha |
| [python-arq/arq](https://github.com/python-arq/arq) / [rq/rq](https://github.com/rq/rq) | MIT/BSD | redis dependency for one concurrent job |
| [davidteather/TikTok-Api](https://github.com/davidteather/TikTok-Api) | MIT | no authenticated routes — useless for private favorites |
| [cdpdriver/zendriver](https://github.com/cdpdriver/zendriver) / nodriver | AGPL-3.0 | in-process Python import, no license boundary possible |
| wkhtmltopdf / imgkit | LGPL | archived 2022, ancient QtWebKit |
| [Kozea/WeasyPrint](https://github.com/Kozea/WeasyPrint) | BSD-3 | PDF-only since v53, no JS |
| [google/nsjail](https://github.com/google/nsjail) | Apache-2.0 | unpackaged for jammy; bwrap+systemd covers it (was PATTERN-ONLY) |
| [netblue30/firejail](https://github.com/netblue30/firejail) | GPL-2.0 | SUID root binary is a net attack-surface increase |
| [google/gvisor](https://github.com/google/gvisor) / minijail | Apache/BSD | syscall tax or ChromeOS-internal ergonomics; nothing over bwrap |
| [zopefoundation/RestrictedPython](https://github.com/zopefoundation/RestrictedPython) | ZPL-2.1 | self-disclaims as a sandbox |
| [containers/podman](https://github.com/containers/podman) | Apache-2.0 | GB images + seconds cold-start per skill call on a small SD |
| [NVIDIA-AI-IOT/nanoowl](https://github.com/NVIDIA-AI-IOT/nanoowl) | Apache-2.0 | ~2GB resident PyTorch+TRT for detection Claude gives free |
| [dusty-nv/jetson-inference](https://github.com/dusty-nv/jetson-inference) | MIT | closed-vocab TRT models answer nothing REMY asks |
| [PaddlePaddle/PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR) | Apache-2.0 | Paddle on aarch64 is a build fight; RapidOCR serves its models |
| fswebcam | GPL-2.0 | archived; v4l2-ctl does it with zero install |
| GongRzhe/Gmail-MCP-Server, servers-archived, isaacphi/mcp-gdrive, executeautomation/mcp-playwright | MIT | archived or superseded by official servers |
| Anthropic computer-use / Claude in Chrome | n/a | API-billed loop needing a display; snapshots are the headless answer |
| E2B / microsandbox | Apache-2.0 | microVMs need KVM, absent from stock L4T kernels |

Verdict changes from 2026-08-05: `modelcontextprotocol/servers` PATTERN-ONLY
-> DEPEND (MCP is now a first-class integration path, not an alt transport);
`google/nsjail` PATTERN-ONLY -> IGNORE; `dusty-nv/NanoLLM` PATTERN-ONLY ->
IGNORE (superseded by ollama on Jetson).

## Coverage

~90 unique repos verified in the 2026-08-05 voice-seeded scan, ~40 more in the
2026-08-06 blind-spot pass (~130 total). Deep dives written for the
highest-value repos scoring >= 3; see `deep-dives/`. Clusters scanned: voice
frameworks, voice apps, pipeline/turn-detection, wake+STT, TTS, self-modifying
agents, agent memory, skills/sandbox/Claude-Code, Jetson/Spotify/dashboards,
MCP, browser control on arm64, vision, job orchestration, secrets/OAuth, and
containment.
