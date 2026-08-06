# Backlog

Ranked and actionable. The **Top 10** are each sized to land as a single PR:
low risk, mostly no new heavy dependencies, and each fixes something known to
be weak. Below them are the bigger bets (multi-PR or risk-carrying), grouped by
theme. Effort is S/M/L; every proposed dependency carries a Jetson Orin Nano
8GB cost note.

## Top 10 — one PR each

### 1. Reconciling memory consolidation
- **Source:** `mem0ai/mem0@3f39fba:mem0/configs/prompts.py:L176-320` (Apache-2.0)
- **Change:** In the idle consolidation pass, after extracting daily facts, run
  mem0's ADD/UPDATE/DELETE/NONE prompt on qwen2.5:3b to emit ops against
  MEMORY.md instead of blind-appending. Stops MEMORY.md drifting into
  self-contradiction.
- **Files:** memory consolidation module, MEMORY.md writer
- **Effort:** S · **Risk:** low (prompt + op-parser; reuses resident qwen) ·
  **New deps:** none

### 2. Semantic end-of-turn detection
- **Source:** `pipecat-ai/smart-turn@4786657` + `pipecat@08f7aed:src/pipecat/audio/turn/smart_turn/base_smart_turn.py:L99-151` (BSD-2); gated by `snakers4/silero-vad` (MIT)
- **Change:** Replace the fixed silence threshold with a silence-gate → 8MB CPU
  ONNX confirm, so REMY stops clipping/over-waiting on turn ends.
- **Files:** STT/turn-detection module, EventBus turn events
- **Effort:** S–M · **Risk:** low · **New deps:** onnxruntime + smart-turn
  ONNX (~8MB) + silero-vad (~2MB); CPU-only, **zero GPU RAM**

### 3. Harden the wake word (no new heavy dep)
- **Source:** `dscripka/openWakeWord@368c037:README.md:L105-115` (Apache-2.0)
- **Change:** Enable `vad_threshold` (silero gate) + `enable_speex_noise_
  suppression=True`; tune threshold; add a DiPCo-style FA/hr + SNR/RIR eval
  script. Kills false activations.
- **Files:** wake-word init/config, new `scripts/eval_wake.py`
- **Effort:** S · **Risk:** low · **New deps:** `libspeexdsp` + speexdsp-ns
  wheel (arm64-supported, negligible RAM)

### 4. Silero pre-clip before Whisper
- **Source:** `rhasspy/wyoming-faster-whisper@5b5854f:vad.py:L1-75` (MIT)
- **Change:** Clip the captured utterance WAV to the speech region (or set
  faster-whisper `vad_filter=True`) to kill silence hallucinations; confirm
  `compute_type=int8`, `cpu_threads=4` on aarch64.
- **Files:** STT module
- **Effort:** S · **Risk:** low · **New deps:** `pysilero-vad` (~1.8MB, few-ms
  CPU) — or zero deps via built-in `vad_filter`

### 5. Pin MIT Piper; block the GPL upgrade
- **Source:** `rhasspy/piper@73c04d` (MIT) vs `OHF-Voice/piper1-gpl@ffb622` (GPL-3.0)
- **Change:** Pin `piper-tts` to the last MIT release and add a CI/comment
  guard so `pip install -U` can't pull GPL-3.0 Piper into REMY's MIT process.
  A live license landmine — the maintained Piper is now GPL.
- **Files:** requirements/pyproject, TTS module
- **Effort:** S · **Risk:** low (prevents a licensing risk) · **New deps:** none

### 6. Align SKILL.md to the Agent Skills spec (as a superset)
- **Source:** `anthropics/skills@b29e7cf` spec (Apache-2.0)
- **Change:** Enforce the spec's `name` regex + "name matches dir" +
  `description` <=1024; nest REMY-specific fields (`triggers`/`watch`/`inject`/
  `handler`) under `metadata:`/`x-remy:` so a stock loader still parses REMY
  skills. Add a validator.
- **Files:** skill loader/parser, SKILL.md schema
- **Effort:** S · **Risk:** low · **New deps:** none

### 7. Fix the hot-reload submodule leak
- **Source:** `OpenVoiceOS/ovos-workshop@7aaa4c5:ovos_workshop/skill_launcher.py:L34-40` (Apache-2.0)
- **Change:** Add `remove_submodule_refs()` before reloading a script skill so
  a reloaded skill fully re-imports (Python caches submodules; REMY's
  mtime-reload almost certainly leaves stale refs). Optionally swap
  per-utterance mtime polling for an inotify watcher.
- **Files:** skill hot-load path
- **Effort:** S · **Risk:** low · **New deps:** none (inotify optional)

### 8. Two-stage acceptance gate + last-known-good *list*
- **Source:** `jennyzzt/dgm@a565fd2:utils/evo_utils.py:L96-127`, `DGM_outer.py:L50-109` (Apache-2.0)
- **Change:** Split the self-mod gate into (1) compiles/`--selftest` passes and
  (2) "actually does X"; reject no-op empty diffs; keep a *list* of
  last-known-good commits (not one) so REMY can branch from a better ancestor
  on repeated failure.
- **Files:** selftest gate, EVOLUTION.md schema, rollback logic
- **Effort:** M · **Risk:** low · **New deps:** none (git + metadata)

### 9. Live overseer/watchdog for self-edit sessions
- **Source:** `MaximeRobeyns/self_improving_coding_agent@ed8275d:base_agent/src/oversight/overseer.py:L42-165` (MIT)
- **Change:** Wrap the headless Claude Code session with a loop/time/budget
  watchdog that force-cancels + rolls back a thrashing session *before* it
  finishes. Heuristic on Jetson: repeated identical tool calls or a wall-clock/
  token budget (no LLM overseer needed).
- **Files:** self-edit session supervisor
- **Effort:** S · **Risk:** low · **New deps:** none

### 10. qwen `<functioncall>` intent prompt
- **Source:** `acon96/home-llm@50cf35c:docs/Model Prompting.md:L6-28` (technique; repo license custom — pattern only)
- **Change:** Adopt the `<functioncall>` system-prompt template with **Minimal**
  tool serialization + in-context examples for the qwen2.5:3b intent path. More
  reliable structured calls, and fewer tokens = *faster* on CPU.
- **Files:** intent/qwen prompt module
- **Effort:** S · **Risk:** low · **New deps:** none (prompt-only; do not copy
  repo code — the technique is what's reused)

## Bigger bets (multi-PR or risk-carrying)

### STT / audio
- **GPU STT via whisper_trt** — `NVIDIA-AI-IOT/whisper_trt@268eff1` (MIT). Add a
  whisper_trt backend behind the STT interface; A/B vs faster-whisper, keep the
  latter as fallback. **M · Risk: medium** (unmaintained since 2024-10; verify
  against JetPack r36 / TensorRT 10; one-time engine build). Deps: torch2trt +
  tensorrt + torch-CUDA (JetPack ships them); ~439MB resident, **frees the CPU**.
- **Streaming partial transcripts** — `usefulsensors/moonshine@cc16956` (MIT-EN)
  or `k2-fsa/sherpa-onnx@00ad9a1` (Apache-2.0). Emit partials to EventBus/TUI;
  keep whisper/whisper_trt for the final. **M.** Deps: moonshine tiny 34M ONNX
  (arm64, CPU) or sherpa-onnx (Jetson GPU/CPU). Optionally layer
  `ufal/whisper_streaming` LocalAgreement over whisper_trt.
- **Voice barge-in** — `dnhkng/GlaDOS@8f19b74:speech_listener.py:L184-204` (MIT).
  Pre-activation ring buffer; cancel Piper mid-stream on VAD. **M · Risk:
  medium** — needs a cancellable Piper stream and, for true open-mic, acoustic
  echo cancellation (`TEN-Agent` pattern + external WebRTC AEC3/speexdsp), which
  is the one thing the scan found no clean lift for. Ship the cancellable-TTS +
  thread-safe stop (`KoljaB/RealtimeTTS`) first.

### Routing / pipeline
- **Tiered local intent router** — `OpenVoiceOS/ovos-core@91021e7:docs/pipeline.md`,
  `dispatcher.py` (Apache-2.0). Ordered matchers resolve cheap commands locally;
  only unmatched utterances hit Claude Code. Add the single-terminal +
  per-handler timeout contract. **M · Risk: low.** No deps. Cuts latency and
  Claude Max usage.
- **Rich pipeline event taxonomy** — `home-assistant/core@6605963:.../assist_pipeline/pipeline.py:L385-412` (Apache-2.0, pattern). Emit
  `STT_VAD_START/END`, `INTENT_PROGRESS`, `TTS_START/END`. **M.** No deps.
- **Wyoming Event envelope + PipelineStage enum** — `rhasspy/wyoming@bf65f4e:event.py`, `pipeline.py` (MIT). ~100 LOC vendorable; enables a
  future satellite/server split to offload a model off the 8GB box. **S.**

### Self-mod / skills
- **Repo-map for self-edit context** — `Aider-AI/aider@5dc9490:aider/repomap.py` (Apache-2.0). Feed a token-budgeted,
  PageRank-ranked map of REMY's own repo into each self-edit session,
  personalized toward the target module. **M.** Deps: `grep-ast`,
  `tree-sitter`, `networkx`, `diskcache` — all pip/arm64, no GPU, ~tens of MB.
- **bubblewrap sandbox for skill execution** — `containers/bubblewrap@2f55bae` (LGPL-2.0+, wrap the binary). Run every `action.command`/`handler`/`requires.pip`
  under `bwrap --unshare-all --ro-bind ...`; opt-in net via the spec
  `compatibility` field. Turns "no shell" into a real boundary. **M.** Deps:
  `bubblewrap` apt pkg (arm64, ~200KB, no VM). Keep it a separate process — do
  not link the LGPL C.
- **can_use_tool permission gate** — `anthropics/claude-agent-sdk-python@71142da:src/claude_agent_sdk/types.py:L238-258` (MIT).
  Drive Claude Code via `ClaudeSDKClient` (inherits Max subscription auth, no
  API key); gate self-mod with the typed `CanUseTool` callback; avoid
  `bypassPermissions`/`allowed_tools` silently shadowing the gate. **M.** Deps:
  `claude-agent-sdk` (pure Python).
- **Embedding skill retrieval + count-invariant** — `MineDojo/Voyager@55e45a8:voyager/agents/skill.py:L64-140` (MIT). Index SKILL.md
  descriptions; retrieve top-k per request; assert index-count == skill-count.
  **M · Risk: RAM.** Deps: local `sentence-transformers` MiniLM (~90MB) — a
  resident embedder to weigh against the 8GB budget; only worth it once skill
  count is high.
- **Pluggy-style loader + `is_blocked` quarantine** — `pytest-dev/pluggy@f632a4d:_hooks.py:L44-75` (MIT). `firstresult`/`tryfirst`/
  `trylast` for trigger resolution + an in-memory blocked-set over the `.failed`
  rename, with an `unblock` recovery command. **M.**
- **Cascade evaluation ordering** — `codelion/openevolve` (Apache-2.0). Run the
  cheapest checks first (import/`--selftest` smoke) before pip-install + full
  skill selftest. **S.**

### Memory
- **Self-edit memory tool for the agent** — Anthropic memory tool + `letta-ai/letta@ff19ffe:.../function_sets/base.py:L246-520` (Apache-2.0). Expose
  `str_replace`/`insert`/`append` over SOUL/USER/MEMORY.md to Claude Code with a
  "view memory first / assume interruption" system prompt and a `/memories`
  path guard. **M.** No deps (native Claude Code loop).
- **Memory blocks: size limit + read_only** — `letta@ff19ffe:letta/schemas/block.py:L18-46` (Apache-2.0). Char `limit` +
  `read_only` marker per SOUL/USER section. **S.** No deps.
- **Decay/reinforcement pruning** — `caspianmoon/memoripy@ffa11da` (Apache-2.0).
  Recency×access-count scalar to prune/promote MEMORY.md entries during idle.
  **S.** No deps (no embeddings).
- **Structured profile + event timeline** — `memodb-io/memobase@358c16b`
  (Apache-2.0). Shape USER.md as a profile schema and the episodic store as a
  time-ordered event log to answer "when" questions without vectors. **S.**

### Jetson / integrations
- **Prebuilt r36 model images** — `dusty-nv/jetson-containers` (Apache-2.0*).
  Base on `dustynv/ollama|faster-whisper|wyoming-openwakeword:*-r36.x` instead
  of source builds; adopt the Wyoming compose topology for per-model memory
  isolation. **M.** Disk ~3-5GB/image; no extra runtime RAM.
- **Spotify via go-librespot sidecar** — `devgianlu/go-librespot@48dd7c1:API.md` (GPL-3.0, process boundary). Replace the Web-API OAuth-app path with local
  REST + `/events` WS for now-playing. **S-M.** Deps: one Go binary (~15MB,
  arm64); Premium still required, app registration dropped. Keep it a sidecar to
  preserve REMY's MIT.
- **Unify frontends with `textual serve`** — `Textualize/textual` (MIT). Serve
  the TUI in-browser; shrink the PWA to the mic button + phone TTS. **M.** Deps:
  `textual-serve` (pure Python).
- **Optional Kokoro voice (CPU/ONNX)** — `thewh1teagle/kokoro-onnx@98ea02` (MIT
  code + Apache-2.0 weights). Selectable alternate voice behind the existing
  streaming iface, Piper stays default. **M · Risk: RTF.** Deps: kokoro-onnx +
  onnxruntime, ~300MB model, +0.5-1GB RAM at synth — **gate on a real Orin RTF
  benchmark first** (borderline in 8GB).

### Novel (no prior art found)
- **Memory-pressure model supervisor** — no repo solves this. Priority-based
  unload of LLM/ASR/TTS under RAM pressure, using Ollama `keep_alive`/unload +
  free-RAM polling. **M-L.** No new deps. This is REMY's open ground.
