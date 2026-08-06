# REMY — Full Architecture + Prior-Art Briefing

A single self-contained document to paste into a chat when deciding what to add
to REMY. **Part 1** is exactly what REMY is and does today, read from the source
(not the READMEs), as detailed as the code allows. **Part 2** is the prior-art
landscape: ~90 verified repos, what to steal, and a ranked backlog. Read Part 1
to know the ground truth; read Part 2 to decide what's worth adding.

- Scanned: 2026-08-06 · REMY is MIT · Jetson Orin Nano 8GB · Python 3.10 · arm64

---

# PART 1 — What REMY is and does (from the code)

## 1. One paragraph

REMY is a self-hosted voice assistant on a Jetson Orin Nano (8GB) that can
rewrite its own code by voice. Wake word, speech-to-text, and quick chat run
fully on device; anything requiring real work spawns a headless Claude Code CLI
session billed to the owner's Claude subscription (no API key). Every component
publishes to an async EventBus; a Textual TUI and a LAN web/PWA dashboard are
just subscribers. Skills are hot-loaded `SKILL.md` folders. Self-modification is
gated by a selftest, git commits, and a crash-loop auto-revert. The default
identity is name "Remy" / owner "Chud", but the wake model defaults to
`hey_jarvis` and the persona is a dry butler — the code class is `Jarvis`.

## 2. Hardware and hard constraints (from CLAUDE.md + code)

- Jetson Orin Nano 8GB, JetPack r36, Ubuntu 22.04, aarch64, Python 3.10.
- **numpy must stay <2** (tflite-runtime crashes on 2.x).
- **Mic capture is `arecord` via subprocess only** — never PyAudio.
- **openWakeWord needs int16 audio** — float32 silently scores ~0.
- **Whisper is CPU-only** — pip CTranslate2 has no aarch64 CUDA.
- 8GB shared between whisper + qwen2.5:3b + piper — no room for another resident
  model. This constraint drives almost every design decision.

## 3. The voice pipeline (end to end)

```
arecord → openWakeWord → (record until silence) → faster-whisper
   → intent router → { fast skill | local chat | Claude Code agent }
   → Piper TTS → aplay        (everything narrated on the EventBus)
```

`handle_text()` in `app.py` is the **single entry point** for an utterance —
voice, TUI input, dashboard `say` message, and stdin all converge there, so
every surface runs the identical pipeline. One `asyncio.Lock` (`_route_lock`)
means exactly one utterance is in the pipeline at a time.

### Audio capture (`audio/capture.py`)
- A dedicated thread owns the mic (arecord reads block). Loop: read 80ms chunk →
  publish a decimated RMS level for UIs → run wake detection → on wake, record an
  utterance and hand `float32` audio back to asyncio via `run_coroutine_threadsafe`.
- **Record-until-silence:** append chunks until `silence_secs` (default 1.5s) of
  sub-`silence_rms` (default 500) audio, or `max_record_secs` (default 10s).
- **Self-trigger avoidance:** the loop is `pause()`d while REMY speaks and
  `resume()`d after — it never hears its own TTS. (This is the only "barge-in":
  the wake word interrupts speech; you cannot interrupt by just talking.)
- **Brief mode:** `extend_next(silence_secs=4, max_secs=180)` is a one-shot
  override so the owner can talk at length.
- Mic-drop resilience: on read failure it publishes an error, waits 3s, and
  `reopen()`s rather than spinning hot.

### Wake (`audio/wake.py`, `openWakeWord`)
- Default model `hey_jarvis_v0.1`, `tflite` framework, threshold `0.3`. Custom
  `.tflite`/`.onnx` paths supported (keyed by filename stem).
- Feeds **int16** chunks; returns a score only when it crosses threshold, then
  `reset()`s. Runs on defaults — **no `vad_threshold` gate, no Speex noise
  suppression, no verifier model** (all available in the dependency, unused).

### STT (`audio/stt.py`, `faster-whisper`)
- Model `base`, `device=cpu`, `compute_type=int8`, `beam_size=1`, `language=en`.
  `base/int8` is the chosen accuracy/latency sweet spot; `tiny` mishears.
- **Utterance-complete, not streaming.** ~1s of dead air after you stop. No VAD
  pre-clip, so it can hallucinate on trailing silence.

### TTS (`audio/tts.py`, `Piper`)
- **Uses the `piper1-gpl` Python API** (`from piper import PiperVoice,
  SynthesisConfig`). Voice `en_GB-alan-medium`. Model loaded once at startup +
  a silent warmup so the first reply isn't slow.
- Streams sentence-by-sentence to `aplay` (raw S16_LE); **interrupt = kill the
  aplay sink**, not the model.
- **LIVE LICENSE NOTE:** importing `piper1-gpl` in-process links GPL-3.0 code
  into MIT REMY. This is a real license conflict today, not hypothetical (see
  Part 2, "license landmines"). Pin the MIT `rhasspy/piper` release, or move
  Piper to a subprocess.

## 4. The EventBus (`events.py`)

The spine. Every component publishes immutable `Event(type, data, ts)`; TUI, web
UI, and logs are all just async-queue subscribers.

- **11 event types:** `STATE, AUDIO_LEVEL, WAKE, TRANSCRIPT, RESPONSE,
  AGENT_START, AGENT_OUTPUT, AGENT_DONE, SKILL, ERROR, SPEAKING`.
- **6 states:** `IDLE, LISTENING, TRANSCRIBING, THINKING, WORKING, SPEAKING`.
- **Backpressure:** on a full subscriber queue it drops the *oldest* event so a
  stalled websocket never blocks the voice pipeline.
- `publish_threadsafe()` bridges the audio thread to the asyncio loop.
- (Gap vs Home Assistant: no fine-grained `STT_VAD_START/END` or
  `INTENT_PROGRESS` events — the UI can't show precise turn-taking.)

## 5. Routing — the full decision tree (`app.py::_route` + `router/intents.py`)

The router is **pure regex, no I/O, unit-tested** (`router/intents.py`). The
orchestrator applies it in this exact order:

1. **Brief mode pending?** → the whole utterance becomes an `agent.task`
   instruction (with the confirm gate).
2. **Confirmation pending?** (a queued agent task) → `yes` runs it, `no`
   cancels, anything else falls through as a fresh command.
3. **Follow-up window?** If a script skill handled the last utterance within
   120s, it gets first refusal via `converse(text) -> str|None` (OVOS-style
   multi-turn).
4. **`parse(text)` intents**, in order:
   - `self.rollback` ("undo/revert/roll back")
   - `self.iterate` ("upgrade/improve/modify/teach/give **yourself** …")
   - `identity.self` / `identity.name`
   - `chat.reset` ("forget that / new topic / clean slate") → raises a context floor
   - `memory.remember` ("remember that …") / `memory.recall` ("what do you remember about …")
   - `system.status` ("status report / sitrep")
   - `spotify.*` (volume set/delta, now-playing, next, pause, resume,
     play_playlist, play_track)
   - `brief.start` ("take a brief / I have a project") → extends next recording
   - `agent.continue` ("continue / keep going")
   - `agent.task` (starts with `edit|create|build|write|deploy|refactor|debug|
     implement|update|fix the/my/a/an …`)
   - else → `chat`
5. **Hot-loaded workspace skills** (`skills.find`) — checked *before* chat.
6. **Escalation lane:** if nothing above handled it, `escalate` is on, Claude is
   available, and a tiny local-LLM triage (`_is_actionable`) says it's an action
   request → `agent.solve` (grow a skill for it; see §7).
7. **Default: local chat** — working memory + episodic recall + keyword-matched
   knowledge skills, streamed sentence-by-sentence into TTS.

Confirmation gates: `self.iterate`, `agent.task`, and `agent.solve` all require
a spoken "yes" when `claude.confirm_tasks` is true (default).

## 6. The two brains

### Local chat (`brain/chat.py`)
- Two providers, one code path: **ollama** (`/api/generate`, default
  `qwen2.5:3b`) or **openai** (any `/v1/chat/completions`: llama.cpp, vLLM, LM
  Studio, Groq, OpenRouter, Together, OpenAI). stdlib `urllib` only.
- **Streaming:** tokens are split into complete sentences as they arrive so TTS
  starts on the first sentence. `num_predict=150`, `temperature=0.8`.
- **Jetson-specific:** `keep_alive=24h` keeps the model resident; a transient
  HTTP 500 (shared-memory OOM during model load) is retried once after 2s.
- A 128-entry response cache short-circuits repeats.

### Claude Code agent (`brain/claude.py`)
- Runs `claude -p <prompt>` as an **argv subprocess (no shell — injection-safe)**
  with `--output-format stream-json --verbose`.
- Permission model: `--permission-mode acceptEdits`, `--allowedTools
  Read,Edit,Write,Glob,Grep,WebFetch,WebSearch` — **no Bash by default** (a
  misheard command must not run arbitrary shell). Web tools let synthesis
  sessions read real API docs.
- `--continue` resumes the most recent session (for "keep going"/repair);
  `--mcp-config` gives sessions inherited MCP tools; `--append-system-prompt`
  injects persona + task brief.
- **Auth = the owner's Claude subscription** via `CLAUDE_CODE_OAUTH_TOKEN`
  (one-time `claude setup-token`), no per-token API billing. Timeout 600s.
- Parses stream-json into `AgentLine(kind=text|tool|result|error)`; the UI shows
  live tool/text progress, the final `result` line is summarized to ~2 sentences
  for voice.

## 7. Escalation / solve-then-absorb (`app.py::_execute_agent_intent`)

The headline capability. An actionable request nothing handles becomes
`agent.solve`: REMY says "On it", spawns a self-iterate session instructed to
**create a workspace skill** for the request (so it works now and every time
after), the harness activates the skill (installs pip deps, runs selftest,
quarantines failures), then REMY **re-runs the original utterance live** through
the now-loaded skill. This is what makes arbitrary new capabilities possible by
voice.

## 8. Skills (`skills/loader.py`, `skills/activate.py`)

A skill is a directory under `~/.remy/skills/` with a `SKILL.md` (YAML
frontmatter + markdown body). **Rescanned every utterance with an mtime cache** —
new/edited skills take effect immediately, no restart.

**Frontmatter fields:** `name`, `description`, `triggers` (case-insensitive
regex list), `action.command` (bash snippet; utterance in `$REMY_TEXT`, stdout
is spoken) OR `action.script` (`handler.py` exposing `handle(text)->str`),
`requires.bins`/`requires.env`/`requires.pip`, `watch.interval_secs`, `inject`
(keywords).

**Four skill kinds (mixable):**
- **voice** — trigger phrases run a command/handler.
- **watcher** — runs on a schedule (min 60s); speaks only when output *changes*
  (an alarm clock repeats; a good watcher doesn't). Never interrupts a
  conversation.
- **knowledge** — `inject` keywords push the markdown body into chat context for
  that turn (no action).
- **follow-up** — `handler.py` may define `converse(text)->str|None` to claim the
  next utterance for 120s (multi-turn flows without LLM routing).

**Command execution:** `bash -c` with a locked-down env (`PATH`, `REMY_TEXT`,
`HOME` only), 30s timeout, cwd = skill dir. **Script execution:** imports the
sibling file fresh and calls `handle`. A broken skill returns an error string,
never crashes routing.

**Activation & quarantine (`activate.py`) — the harness, not the agent:**
installs `requires.pip`, imports `handler.py`, runs its `selftest()` if present;
on any failure renames `SKILL.md → SKILL.md.failed` so the loader never sees it.
The agent has **zero shell access** at any point. `catalog()` (one line per
skill) is injected into agent briefs so REMY knows what it can already do and
extends rather than duplicates.

## 9. Self-modification (`skills/selfiterate.py` + `supervisor.py`)

Flow for "upgrade yourself …":
1. Snapshot `HEAD`.
2. Headless Claude Code session edits the repo, guided by `_AGENT_BRIEF`
   (prefer a workspace skill; for real integrations research the API via
   WebFetch, write `handler.py`, declare pip deps, include a `selftest()` making
   one cheap real call; keep changes minimal; py3.10/numpy<2/arecord; **don't
   run the app, install packages, or touch git — the harness does that**).
3. Activate any skills the agent wrote (pip + selftest + quarantine).
4. If the repo changed: run `python3 -m remy --selftest` (imports every module +
   runs pytest `tests/`). **Repair-before-rollback:** on failure, one bounded
   repair attempt feeds the selftest output back into the same session via
   `--continue`; re-test. If still failing, **hard-reset to the snapshot** and
   discard.
5. On pass: `git commit` (prefix `self: `), `record_good(before)` as the
   fallback, append to `EVOLUTION.md` (when / what asked / result / ref), then
   **restart in place** (`os.execv`). Workspace-only changes skip the restart.
- "Undo that" (`rollback`) hard-resets `HEAD~1` only if the last commit was a
  `self:` commit, then restarts.

**Boot guard (`supervisor.py`):** every boot increments a counter;
`mark_healthy()` (called 60s after a successful start) resets it. If the app
boots >3 times without ever reaching healthy (`crash_looping()`), the **next
boot auto-reverts** the repo to the recorded last-good ref *before importing the
package* — which is why `__main__.py` runs the guard before any other import.

## 10. Memory (`brain/episodic.py`, `workspace.py`)

**One episodic store, three layers (no vector DB, no embeddings — keyword search
with recency boost):**
- `memory/episodes.jsonl` — every turn (user/reply/intent/ts), reply capped 1000
  chars.
- `memory/DATE.md` — daily summaries written during idle "sleep" consolidation.
- `MEMORY.md` — curated long-term facts (semantic memory).

- **Working memory:** last **6 turns within a 600s TTL**, rendered into the chat
  prompt. "forget that / new topic" raises a `_context_floor` that hides earlier
  turns.
- **Recall search:** keyword overlap scored `overlap / (1 + age_days*0.1)`,
  **skipping the working-memory window** so the current conversation isn't echoed
  back. Separate search over daily summaries (tagged with date, so "when"
  questions work).
- **Consolidation (idle > 30 min):** take the oldest unconsolidated day → qwen
  writes a `## Summary` + `## Facts` markdown → save `DATE.md` → **fold** the
  non-duplicate Facts into `MEMORY.md` with a `<!-- consolidated DATE -->`
  marker. (Append-only — **no reconciliation**: stale/contradictory facts are
  never updated or deleted. This is a known weak spot; see Part 2.)
- **Persona files** (`workspace.py`): `SOUL.md` (persona), `USER.md` (owner),
  `MEMORY.md` — injected into *every* brain call (local + Claude). `fast` mode
  hard-caps them (1200/600/2400 chars) because every KB is prefill latency on the
  3B model. The agent can edit these files, which is how "change your
  personality" works with no code change. "remember that X" appends straight to
  `MEMORY.md`.

## 11. Spotify (`skills/spotify.py`)

Official Web API with OAuth tokens at `~/spotify_tokens.json` (access + refresh
+ client creds), stdlib `urllib`, auto-refresh on 401. Intents: play track
(search+play), play playlist (fuzzy match over your 50 playlists), next, pause,
resume, now-playing, volume set/delta. **Requires a registered Spotify developer
app + Premium** (the app-registration path go-librespot would remove — Part 2).

## 12. Surfaces

- **TUI** (`tui/app.py`, Textual): block-letter state, VU meter, conversation +
  agent panes, input box.
- **Web/PWA dashboard** (`server/app.py`, FastAPI + uvicorn, `:8484`): serves the
  PWA (manifest + icon), streams events over `/ws`, and the socket is
  **bidirectional** — a client `{"type":"say","text":...}` runs the same
  pipeline as voice (phone mic button). `/preview` statically mounts
  `~/.remy/preview` so agent-produced mockups/variants are reviewable on the LAN.
  Optional `server.auth_token` (hmac-compared `?key=`).
- **Headless** (`--headless`): console + stdin, for systemd/scripting.
- **Two frontends today** (TUI + hand-rolled PWA) — `textual serve` could
  collapse most of the duplication (Part 2).

## 13. Config surface (`config.py`, all in `config.toml`, env-overridable)

Sections and the load-bearing knobs:
- `[identity]` name / owner.
- `[projects]` `name = "path"` — "edit my portfolio …" runs the agent in that dir.
- `[audio]` mic/speaker device, sample_rate 16000, chunk 1280 (80ms),
  silence_rms/secs, max_record_secs.
- `[wake]` model (`hey_jarvis_v0.1`), framework (`tflite`), threshold (0.3).
- `[stt]` model (`base`), device (`cpu`), compute_type (`int8`), beam_size (1),
  language (`en`).
- `[tts]` enabled, voice (`en_GB-alan-medium`), voices_dir, length_scale.
- `[chat]` provider (`ollama`/`openai`), url, model (`qwen2.5:3b`), num_predict
  (150), temperature (0.8), keep_alive (24h), api_key_env, system_prompt.
- `[claude]` binary, workdir (`~/remy`), timeout (600s), **allowed_tools (no
  Bash)**, permission_mode (`acceptEdits`), **confirm_tasks** (true),
  mcp_config, **heartbeat_hours** (0=off), **escalate** (true).
- `[spotify]` token_file.
- `[server]` host, port (8484), auth_token.

## 14. Operations

- `--doctor` checks mic/speaker/wake/voice/chat/claude/Spotify with fix commands.
- `--selftest` = import every module + run pytest `tests/` (the self-mod gate).
- "status report" speaks uptime, skill count, episode count, long-term fact
  count, free RAM/disk, last-turn STT + first-reply latency.
- systemd unit, idempotent installer, crash-loop auto-revert.
- **Heartbeat:** `~/.remy/HEARTBEAT.md` run as a standing agent instruction on a
  cadence; replies `HEARTBEAT_OK` when nothing needs attention (silent), else
  speaks. Background loop also runs due watchers and memory consolidation.

## 15. Known weak spots (REMY's own gaps, tie into Part 2)

- **No barge-in by voice** (turn-locked by non-streaming Whisper; only the wake
  word interrupts). No echo cancellation.
- **End-of-turn is a fixed silence threshold** — clips or over-waits.
- **STT is CPU-only and non-streaming** (~1s dead air; no GPU path; no VAD
  pre-clip → silence hallucinations).
- **Wake word runs on defaults** — false-accept levers unused.
- **No local intent router tier** beyond regex — everything unmatched escalates.
- **Memory consolidation never reconciles** — MEMORY.md drifts.
- **"No shell" is a policy, not a sandbox boundary.**
- **Model-swap under 8GB pressure is unsolved.**
- **TTS links GPL Piper in-process** (license conflict).

---

# PART 2 — Prior-art landscape (what to steal)

~90 repos verified via `gh api` (stars/last-commit/license/issues), 34 written
up in full under `docs/research/deep-dives/`. Full tables in
`docs/research/index.md`; honest assessment in `gaps.md`; ranked work in
`backlog.md`. Condensed here for decision-making.

## Verdicts
**VENDOR** copy code (permissive) · **PORT** reimplement the pattern · **DEPEND**
add a dependency · **PATTERN-ONLY** ideas only (license/weights forbid vendoring)
· **IGNORE**.

## License landmines (act on these)
- **REMY already imports GPL-3.0 `piper1-gpl` in-process** (see Part 1 §3). Pin
  `rhasspy/piper` (MIT, archived) or run Piper as a subprocess. The maintained
  Piper is GPL; a naive `pip -U piper-tts` deepens the conflict.
- TTS with real quality (F5-TTS, XTTS/Coqui) carry **non-commercial *weight***
  licenses separate from code; Orpheus is a 3B model. All pattern-only / won't
  fit 8GB. **No MIT-clean, CPU-feasible voice-cloning TTS exists** — a real gap.
- go-librespot / spotifyd are GPL → sidecar (separate process) only.

## Top candidates by area

**Turn-taking / barge-in (REMY's #1 UX gap)**
- `pipecat-ai/smart-turn` (BSD, VENDOR) — 8MB CPU ONNX semantic end-of-turn,
  ~10-100ms, zero GPU. The lightest fix for clip/over-wait.
- `snakers4/silero-vad` (MIT, DEPEND) — ~2MB ONNX, <1ms/chunk; the VAD gate for
  turn detection and barge-in.
- `dnhkng/GlaDOS` (MIT, VENDOR) — production barge-in: pre-activation ring buffer
  + gap-counter turn end; cancel TTS on VAD. `speech_listener.py:L40-44,184-221`.
- `pipecat-ai/pipecat` (BSD, PORT) — `MinWordsUserTurnStartStrategy(min_words=3)`
  so backchannels don't false-interrupt.
- `livekit/agents` (Apache, PORT) — *text*-based end-of-turn over the transcript
  (complementary to smart-turn; heavier).
- AEC (echo cancellation) for true open-mic barge-in has **no clean lift** —
  `TEN-Agent` shows the architecture but delegates to WebRTC SDKs.

**STT (GPU + streaming)**
- `NVIDIA-AI-IOT/whisper_trt` (MIT, VENDOR) — the one repo built for REMY's exact
  constraint: Whisper on the Orin GPU via TensorRT. `base.en` 0.86s vs 2.55s,
  439MB vs 666MB, **frees the CPU**. Risk: unmaintained since 2024-10, verify on
  r36/TRT10, one-time engine build.
- `usefulsensors/moonshine` (MIT-EN, DEPEND) — streaming partials, arm64, 237ms
  on a Pi5. `k2-fsa/sherpa-onnx` (Apache, DEPEND) — streaming Zipformer + KWS,
  Jetson-supported. `ufal/whisper_streaming` (MIT, PORT) — LocalAgreement policy
  to layer over whisper_trt.
- `rhasspy/wyoming-faster-whisper` (MIT, PORT) — silero pre-clip to kill silence
  hallucinations; correct CPU config (`int8`, `cpu_threads=4`).

**Wake word (already shipped — just tune)**
- `dscripka/openWakeWord` (DEPEND) — turn on `vad_threshold` + Speex NS
  (arm64-supported) + verifier models; adopt the DiPCo FA/hr eval. Issue #335:
  don't blindly augment positive clips for a custom "Remy" word (177 FP/hr).

**TTS**
- `thewh1teagle/kokoro-onnx` (MIT + Apache weights, DEPEND) — the only neural TTS
  that could beat Piper on quality while staying MIT-clean and CPU-only; ~300MB,
  RTF borderline on Orin — gate on a real benchmark. Keep Piper default.
- Pin MIT `rhasspy/piper`; treat `OHF-Voice/piper1-gpl` (GPL) as subprocess-only.

**Self-modification (be skeptical — mechanism is prior art)**
- `jennyzzt/dgm` (Apache, PORT) — Darwin Gödel Machine: self-edit + empirical
  validation + **archive of validated versions**. Beats REMY's single
  last-known-good (branch from any ancestor) and its binary selftest (measures
  *improvement*, not just "didn't break"). `evo_utils.py:L96-127`,
  `DGM_outer.py:L50-109`.
- `Aider-AI/aider` (Apache, VENDOR) — `repomap.py`: tree-sitter + PageRank
  token-budgeted repo map to feed self-edit sessions cheap context.
- `MineDojo/Voyager` (MIT, PORT) — embedding skill retrieval + count-invariant
  (`skill.py:L64-140`) — scales past REMY's flat hot-load.
- `MaximeRobeyns/self_improving_coding_agent` (MIT, PORT) — a live **overseer**
  that cancels a thrashing session *during* execution (`overseer.py:L42-165`) —
  REMY's crash-revert is only post-hoc.
- `SWE-agent` (MIT, PORT) — patch-as-artifact + "is this promising" pre-apply
  gate. `codelion/openevolve` (Apache, PORT) — cascade evaluation (cheap checks
  first). `AutoGPT` — case study of what *not* to do (no gate, no watchdog,
  unbounded shell — REMY's design is the corrective).

**Memory**
- `mem0ai/mem0` (Apache, VENDOR prompts) — ADD/UPDATE/DELETE/NONE reconciliation
  prompt (`prompts.py:L176-320`), runs on qwen, no embeddings. The direct fix for
  MEMORY.md drift.
- `letta-ai/letta` (Apache, PORT) — `Block(value/limit/label/read_only)` +
  self-edit tools + keyword `conversation_search` (no embeddings)
  (`base.py:L246-520`, `block.py:L18-46`).
- **Anthropic memory tool + context editing** (DEPEND, native) — REMY's agent IS
  Claude Code; expose SOUL/USER/MEMORY.md via `str_replace`/`insert` +
  "view-memory-first" discipline.
- `memoripy` (Apache, PORT) decay/reinforcement; `memobase` (Apache, PORT)
  profile + event timeline. Both embedding-free. `zep`/`cognee`/`Memary` = too
  heavy for 8GB (Neo4j/embeddings) — IGNORE.
- **REMY's markdown-native, no-embeddings memory is the correct call for 8GB**,
  validated by letta's keyword search and memobase's SQL-only path.

**Skills / sandbox / Claude Code**
- `anthropics/skills` (Apache, PORT) — align SKILL.md to the Agent Skills spec as
  a superset (nest REMY fields under `metadata`), adopt **progressive
  disclosure** (metadata→body→resources) to save 8GB context.
- `containers/bubblewrap` (LGPL, DEPEND, wrap the binary) — a real kernel
  sandbox that fits Jetson arm64 with no VM; wrap skill execution + pip.
  (`microsandbox`/`E2B` need KVM/cloud — dead ends on-device.)
- `anthropics/claude-agent-sdk-python` (MIT, DEPEND) — `can_use_tool` callback
  *is* REMY's permission gate; subprocessing the CLI inherits the Max
  subscription (no API key) — the sanctioned version of what REMY hand-rolls.
- `pytest-dev/pluggy` (MIT, PORT) — `firstresult`/`tryfirst` dispatch +
  `is_blocked` quarantine, cleaner than method-name probing + `.failed` rename.
- `OpenVoiceOS/ovos-workshop` (Apache, PORT) — `remove_submodule_refs()`;
  **REMY's mtime script-skill reload likely leaks stale submodules today.**

**Pipeline / routing**
- `OpenVoiceOS/ovos-core` (Apache, PORT) — confidence-tiered local router;
  resolve "stop"/skill-owned phrases locally instead of escalating (cuts latency
  + Claude Max usage). `home-assistant/core` (PATTERN) — the `PipelineEventType`
  taxonomy (`STT_VAD_START/END`, `INTENT_PROGRESS`) for a livelier UI.
- `rhasspy/wyoming` (MIT, VENDOR) — ~100-LOC `Event` envelope + `PipelineStage`
  enum; enables a future satellite/server split to offload a model off the 8GB
  box.

**Jetson / integrations**
- `dusty-nv/jetson-containers` (DEPEND) — prebuilt r36 arm64 images for
  ollama/faster-whisper/openWakeWord + a full Wyoming voice-pipeline compose.
  Stop building from source. **No model-swap orchestrator exists** anywhere.
- `devgianlu/go-librespot` (GPL sidecar, DEPEND) — Spotify play/skip/now-playing
  **without app registration** (REST + WS `/events`); Premium still required.
- `Textualize/textual` `serve` (MIT, DEPEND) — one codebase for TUI + browser.

## Where REMY is genuinely novel (skeptical)
- **Voice-driven self-modification with a spoken-yes gate** — nothing else is
  voice-first.
- **A self-modifying agent fully on an 8GB edge device** — DGM/SICA/OpenHands are
  all cloud/Docker/GPU.
- **"Agent has no shell" as the sandbox** — cleaner than isolate-after-the-fact.
- **Claude-Code-billed brain + hot-load SKILL.md** — novel packaging.
- **Markdown-native, human+agent-editable, no-embeddings memory** — right for 8GB.
- **Memory-pressure model swapping** — unsolved by any repo scanned. Open ground.

**But:** the self-mod *mechanism* (edit → verify → rollback) is NOT novel — DGM
published it. Pitch REMY on **deployment** (voice + on-device + no-shell + Claude
Code), not on the mechanism.

## The ranked backlog

**Top 10 (each one PR, low risk, mostly no new heavy deps):**
1. Reconciling memory consolidation (mem0 update prompt) — S, no deps.
2. Semantic end-of-turn (smart-turn 8MB + silero-vad) — S-M.
3. Harden openWakeWord (`vad_threshold` + Speex NS) — S.
4. Silero pre-clip before Whisper (anti-hallucination) — S.
5. Pin MIT Piper / stop linking GPL (**live issue**) — S.
6. Align SKILL.md to the Agent Skills spec (superset) — S.
7. Fix hot-reload submodule leak (ovos-workshop) — S.
8. Two-stage acceptance gate + last-known-good *list* (dgm) — M.
9. Live overseer/watchdog for self-edit sessions (SICA, heuristic) — S.
10. qwen `<functioncall>` intent prompt (home-llm technique) — S.

**Bigger bets:** whisper_trt GPU STT (M, r36 risk) · voice barge-in + AEC (M-L) ·
streaming partials (M) · tiered local router (M) · aider repo-map for self-edit
(M) · bubblewrap sandbox (M) · go-librespot Spotify (S-M) · jetson-containers
images (M) · self-edit memory tool (M) · embedding skill retrieval (M, RAM) ·
`textual serve` (M) · Kokoro voice (M, benchmark first) · HA event taxonomy (M) ·
**memory-pressure model supervisor (novel, no prior art)** (M-L).

## If REMY had bandwidth for three things this month (argued)
1. **Semantic end-of-turn (smart-turn + silero-vad)** — the change you feel every
   conversation; 8MB, license-clean, zero GPU.
2. **Reconciling memory consolidation (mem0 prompt)** — a headline feature that
   silently rots; a prompt + parser on the qwen you already run; highest ROI in
   the backlog.
3. **Harden openWakeWord** — false wakes are the daily annoyance; the fixes are
   already inside the dependency (config + a small eval).

Deliberately not the flashy ones: whisper_trt carries r36 risk (needs on-device
validation), and barge-in isn't good without echo cancellation (the one thing
with no clean lift). Ship these three, then take the whisper_trt bet with the CPU
headroom they buy.

---

## How to use this doc in a chat
Paste it and ask, e.g.: "Given REMY's architecture in Part 1, which three
backlog items compound best?" · "Design the smart-turn integration against
REMY's capture loop and EventBus (Part 1 §3-4)." · "Draft the mem0 reconciliation
step for the idle consolidation in §10." · "Is the GPL Piper issue real and
what's the minimal fix?" The architecture detail in Part 1 is enough to design a
concrete change without re-reading the code.
