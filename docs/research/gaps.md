# Gaps and Novelty

The honest part. Where REMY is behind the field (with the repos that beat it
named), where it is genuinely novel (held to a skeptical standard), and the
three changes worth making this month.

## Where REMY lags

### Turn-taking and latency
- **No barge-in.** REMY's non-streaming Whisper makes the listen loop
  turn-locked; you can only interrupt via the wake word. `dnhkng/GlaDOS`
  (`speech_listener.py:L184-204`) cancels TTS the instant VAD fires using a
  pre-activation ring buffer; `pipecat` adds a `min_words=3` guard so
  backchannels ("mhm") don't false-trigger. Real open-mic barge-in also needs
  acoustic echo cancellation so the mic doesn't hear Piper — `TEN-Agent` shows
  the architecture but delegates AEC to WebRTC SDKs; **no repo offers a clean
  pure-Python AEC lift**, so this stays partly novel work.
- **End-of-turn is silence-only.** REMY waits a fixed silence threshold, so it
  either cuts people off or waits too long. `pipecat-ai/smart-turn` (8MB CPU
  ONNX) and `livekit/agents` (text-based EOU over the transcript) both add
  *semantic* end-of-turn. Either fits 8GB; smart-turn is the lighter win.
- **No streaming / partial transcripts.** Utterance-complete Whisper gives ~1s
  of dead air. `usefulsensors/moonshine` (arm64, MIT-EN, 237ms on a Pi 5),
  `k2-fsa/sherpa-onnx` (streaming Zipformer, Jetson-supported), and
  `KoljaB/RealtimeSTT` all stream. Partly hardware-bound: streaming
  faster-whisper on CPU is awkward.

### STT / wake on the Jetson
- **STT is CPU-only** because CTranslate2 has no aarch64 CUDA build (confirmed
  by whisper_trt's own "Unavailable" benchmark). `NVIDIA-AI-IOT/whisper_trt`
  runs Whisper on the Orin GPU via TensorRT: `base.en` **0.86s vs 2.55s**,
  **439MB vs 666MB** — ~3x faster and lighter, and it frees the CPU that qwen
  contends for. This is REMY's single biggest hardware lag.
- **Silence hallucination.** Utterance-complete CPU Whisper hallucinates on
  trailing silence; `rhasspy/wyoming-faster-whisper` (`vad.py`) pre-clips with
  silero, or set faster-whisper `vad_filter=True` for zero new deps.
- **Wake-word false accepts.** REMY likely runs openWakeWord on defaults and is
  missing its own levers: `vad_threshold` (silero gate), `enable_speex_noise_
  suppression=True` (arm64-supported), custom verifier models, and a DiPCo-style
  FA/hr + SNR/RIR eval. All in the engine we already ship. (Also: openWakeWord
  issue #335 — do **not** blindly apply the augmentation recipe to positive
  clips when training a custom "Remy" word; it collapsed separability to
  ~177 FP/hr.)

### Routing and pipeline
- **No local intent router before the agent.** `OpenVoiceOS/ovos-core` and
  `home-assistant/core` both run a confidence-tiered matcher that resolves
  cheap commands ("stop", skill-owned phrases) *without* the expensive brain.
  REMY routes almost everything to Claude Code — a pre-router would cut latency
  and Claude Max usage.
- **Coarse event vocabulary.** HA's `PipelineEventType` (`STT_VAD_START/END`,
  `INTENT_PROGRESS`) drives precise, live turn-taking UI. REMY's EventBus lacks
  these fine-grained events, so the TUI/PWA feel less alive.

### Self-modification (the differentiator — be skeptical)
- **The mechanism is prior art.** `jennyzzt/dgm` (Sakana's Darwin Gödel
  Machine, arXiv:2505.22954) is a coding agent that rewrites its own code,
  validates each change empirically, and keeps an archive of validated
  versions. REMY's "self-modify + verify + keep last-known-good" is **not novel
  as a mechanism** — DGM did it first and published. Do not pitch it as new.
- **Single last-known-good is weaker than an archive.** DGM (`DGM_outer.py:
  L50-109`) and `self_improving_coding_agent` keep a full lineage and select a
  parent by score; REMY keeps one slot and can't branch from a better ancestor.
- **A binary `--selftest` only proves "didn't break."** DGM and `openevolve`
  gate on *measured improvement* (accuracy delta, cascade eval) — "actually got
  better," not just "still runs."
- **No live overseer.** REMY's crash-loop revert is post-hoc; `self_improving_
  coding_agent`'s `overseer.py:L42-165` cancels a looping/thrashing session
  *during* execution before it burns budget.
- **Flat skill hot-load doesn't scale.** `MineDojo/Voyager` (`skill.py:L64-140`)
  embeds skill descriptions and retrieves top-k; REMY loads every SKILL.md.
- **Ad-hoc code context.** `Aider-AI/aider` (`repomap.py`) hands the agent a
  ranked, token-budgeted repo map; REMY leans on Claude Code's default file
  discovery when it edits itself.

### Memory
- **No reconciliation.** REMY's idle pass folds facts in but never
  updates/deletes stale ones, so MEMORY.md drifts and contradicts. `mem0`'s
  ADD/UPDATE/DELETE/NONE prompt (`prompts.py:L176-320`) is the fix, and it runs
  on qwen2.5:3b with no embeddings.
- **No in-loop self-edit.** `letta` and Anthropic's memory tool let the *agent*
  write durable facts via `core_memory_append`/`str_replace`; REMY only
  consolidates out-of-band on idle. REMY's agent *is* Claude Code, which has a
  native file-memory tool it isn't using.
- **No size governor / decay / temporal model.** `letta`'s `Block(limit,
  read_only)`, `memoripy`'s decay+reinforcement, and `memobase`'s profile +
  event timeline are each small, embedding-free upgrades REMY lacks.

### Skills and sandbox
- **"No shell" is a policy, not a boundary.** `containers/bubblewrap` gives
  kernel-enforced isolation (user namespaces + seccomp) that fits Jetson arm64
  with no VM — the real sandbox REMY should wrap skill execution in.
  (`microsandbox`/`E2B` are confirmed dead-ends on-device: KVM/cloud.)
- **No progressive disclosure.** `anthropics/skills` splits metadata → body →
  resources; REMY loads whole SKILL.md per utterance, wasting context on 8GB.
- **Hot-reload likely leaks stale submodules.** `ovos-workshop`'s
  `remove_submodule_refs()` is the fix REMY's mtime-reload is missing.
- **No frontmatter validation** vs the Agent Skills `name`-regex + dir-match.

### Jetson / integrations
- **Building models from source** vs `dusty-nv/jetson-containers` prebuilt r36
  arm64 images for ollama/faster-whisper/piper/openWakeWord.
- **Spotify needs the official Web API + app registration.**
  `devgianlu/go-librespot` (REST + WS sidecar) removes that (Premium still
  required by Spotify, but no developer-app dance).
- **Two frontends.** `textual serve` collapses most of the TUI+PWA duplication;
  only the phone mic button / phone-side TTS is genuinely PWA-specific.

## Where REMY is genuinely novel

Held skeptically — most "novelty" claims collapsed under the scan. What
survives is about **deployment**, not mechanism:

- **Voice-driven self-modification with a spoken-yes gate.** Nothing in the
  self-improving-agent cluster is voice-first or uses spoken confirmation as
  the human-in-the-loop. This is the real differentiator.
- **A self-modifying agent that runs fully on an 8GB edge device.** DGM, SICA,
  OpenHands, SWE-agent all assume cloud/Docker/GPU-server infra. On-device
  self-rewrite is unclaimed territory.
- **The Claude-Code-billed brain** (headless CLI on a Max subscription, no API
  key) driving hot-loaded SKILL.md skills. `claude-agent-sdk-python`'s
  `can_use_tool` callback is the sanctioned version of REMY's permission gate,
  which validates the approach rather than beating it.
- **Markdown-native, human+agent-editable memory** (SOUL/USER/MEMORY.md).
  mem0/zep/cognee are DB-first; letta only recently added git-backed markdown.
  REMY's is simpler and more transparent — and the **no-embeddings keyword
  recall is the correct call for 8GB**, not a shortcut: every embedding system
  surveyed would cost 130MB–1GB+ of resident RAM against whisper+qwen+piper.
- **Memory-pressure model swapping.** REMY's stated pain — priority-unloading
  whisper/LLM/TTS under 8GB pressure — is solved by *no repo in the scan*.
  jetson-containers gives container isolation and an Ollama memory table but no
  orchestrator. This is genuinely open ground.

Net: position REMY on **voice + on-device + no-shell + Claude Code**, not on
"an agent that edits and verifies itself" — that race was already run.

## If REMY had bandwidth for only three changes this month

**1. Semantic end-of-turn, via `pipecat-ai/smart-turn` (8MB) + `snakers4/silero-vad`.**
This is the change users would feel first. Every conversation today pays the
silence-threshold tax: REMY either clips you mid-thought or sits waiting after
you've finished. smart-turn is a Whisper-tiny + linear head, 8MB int8, runs in
tens of milliseconds on the Orin CPU, competes for nothing on the GPU, and is
BSD-2 (vendorable). silero-vad (MIT, ~2MB, <1ms/chunk) is the gate that feeds
it and the same VAD you'll need for barge-in later. Small footprint, clean
license, immediate and constant payoff. Do this first.

**2. Reconciling memory consolidation, via `mem0`'s update prompt.**
Memory is a headline feature and it silently rots: the idle pass appends facts
and never retracts them, so "favorite color: blue" and "...green" both survive
and MEMORY.md drifts into self-contradiction. mem0's ADD/UPDATE/DELETE/NONE
reconciliation prompt (`prompts.py:L176-320`) drops straight into the existing
idle pass, runs on the qwen2.5:3b REMY already has resident, needs zero new
dependencies and zero embeddings, and turns a feature that degrades over time
into one that improves. It is the highest value-to-effort item in the entire
backlog — a prompt and a small op-parser.

**3. Harden the wake word REMY already ships — openWakeWord `vad_threshold` +
Speex noise suppression.**
False activations are the single most irritating daily failure of any
always-listening assistant, and REMY is almost certainly running openWakeWord
on defaults. The fixes are already inside the dependency: turn on the silero
`vad_threshold` gate and `enable_speex_noise_suppression=True` (both
arm64-supported), tune the threshold against a DiPCo-style false-accept set,
and add the verifier-model hook for high-noise rooms. No new heavy dependency,
no GPU cost, pure configuration and a small eval harness — and it stops REMY
waking up to the TV.

These three are deliberately *not* the flashy ones. The bigger swings —
`whisper_trt` GPU STT and true voice barge-in — are worth doing, but STT-on-TRT
carries real JetPack-r36 compatibility risk that needs on-device validation
time, and barge-in isn't good without echo cancellation, which is the one thing
the scan found no clean lift for. The three above are each a single PR, each
fixes something you feel every day, and none of them gambles the 8GB budget.
Ship them, then take the whisper_trt bet with the CPU headroom they buy you.
