# Architecture

Everything in the system, and every path through it. Written so you can decide what to keep. Each section notes what breaks if you delete that piece.

## The one-paragraph version

An audio thread feeds a wake word model. When it fires, the utterance is recorded, transcribed, and handed to a router as text. The router picks one of five handlers: a built-in skill, a hot-loaded workspace skill, local LLM chat, an agent session, or a memory operation. Every component publishes events to one bus; the TUI, web dashboard, and console are interchangeable subscribers. Replies go out through Piper TTS. A background loop runs scheduled watchers and consolidates memory when idle. Self-modification is an agent session pointed at this repo, gated by the test suite and a git-based rollback ladder.

## Module map

```
jetsonclaw/
  __main__.py        entry point, boot guard, CLI flags
  config.py          all tunables, one frozen dataclass per section
  events.py          EventBus: async pub/sub, the spine
  app.py             Jarvis: the orchestrator, owns everything below
  runner.py          TUI and headless launchers, stdin input
  supervisor.py      boot counting, last-known-good, restart
  workspace.py       ~/.jetsonclaw: persona files, memory files, skills dir
  diagnostics.py     --doctor command
  audio/
    mic.py           arecord subprocess wrapper
    wake.py          openWakeWord (int16 in, score out)
    capture.py       the audio thread: wake watch + record-until-silence
    stt.py           faster-whisper transcription
    tts.py           Piper synthesis streamed to aplay
  router/
    intents.py       pure text -> Intent parsing, no I/O
  brain/
    ollama.py        local chat, streaming, sentence splitting, cache
    episodic.py      EpisodicStore + Consolidator (all memory)
    claude.py        headless Claude Code sessions, stream-json parsing
  skills/
    loader.py        SKILL.md discovery, parsing, hot reload, watchers
    activate.py      pip install + selftest + quarantine for new skills
    spotify.py       Spotify Web API client and handlers
    selfiterate.py   self-modification flow and rollback
  server/
    app.py           FastAPI: dashboard, bidirectional websocket
    static/          dashboard PWA (single index.html), manifest, icon
  tui/
    app.py           Textual UI
    blockfont.py     block letter rendering
```

## Runtime state (all under ~/.jetsonclaw/)

| Path | What | Written by |
|---|---|---|
| `config.toml` | user config | you |
| `env` | secrets and PATH for systemd | you, once |
| `SOUL.md` `USER.md` `MEMORY.md` | persona and long-term facts | you, the agent, consolidation |
| `memory/episodes.jsonl` | every interaction, timestamped | every turn |
| `memory/YYYY-MM-DD.md` | daily summaries | idle consolidation |
| `skills/<name>/SKILL.md` | hot-loaded skills | you or the agent |
| `voices/` | Piper models | installer |
| `boot_count`, `last_good_ref` | crash-loop guard state | supervisor |
| `venv/` | Python environment | installer |

## Workflows

### 1. Voice command (the main loop)

```
audio thread (capture.py)                      event loop (app.py)
  arecord 80ms chunks
  -> wake.detect (int16)
  on fire: publish WAKE, record until
  1.5s silence (RMS < 500), max 10s
  -> on_utterance(float32) ---------------->  transcribe (whisper, thread)
                                              publish TRANSCRIPT
                                              intents.parse(text)
                                              route (serialized by a lock)
                                              respond: publish RESPONSE,
                                              pause mic, speak via Piper, resume
```

Latency budget: wake fire is instant, whisper ~1s, fast-path skills <100ms, first spoken sentence of a chat reply ~1-2s (LLM streams sentence by sentence into TTS).

### 2. Text command

`handle_text()` is the single entry point. Voice lands there after transcription; the TUI input box, the dashboard websocket (`{"type": "say", ...}`), and stdin in headless mode all call it directly. Identical routing, identical events. This is also how everything gets tested without a microphone.

### 3. Routing order (app._route)

1. pending confirmation check (yes / no / anything else falls through as a new command)
2. `identity.*` owner name, assistant name
3. `chat.reset` raise the context floor
4. `memory.remember` append fact to MEMORY.md, `memory.recall` search and answer
5. `spotify.*` playback, search, playlists
6. `self.rollback` revert last self-commit
7. `self.iterate` / `agent.task` queue for confirmation, then agent session
8. workspace skills (loader.find, hot reload by mtime)
9. fallback: local chat with working memory + episodic recall injected

Delete a handler and its intent falls through to chat; nothing else breaks.

### 4. Local chat

Prompt = relevant old episodes (keyword search, recency boosted, skips the last 10 minutes) + last 6 turns + the utterance. System prompt = persona files, hard-capped for prefill speed. Streamed: tokens split into sentences, each sentence goes to TTS while the next generates. Replies cached (128 entries). ollama keeps the model resident 24h.

### 5. Agent task ("edit my portfolio site to ...")

Spoken yes required (config: `claude.confirm_tasks`). Runs `claude -p` headless in `claude.workdir` with stream-json output; tool calls and text stream onto the bus as AGENT_OUTPUT (visible in TUI and dashboard). Default toolset has no Bash. Result is summarized to two sentences for voice.

### 6. Self-iteration ("upgrade yourself to ...")

```
confirm -> snapshot HEAD -> claude session in this repo
        -> agent brief says: prefer a workspace skill; repo code only for core changes
        -> harness activates any new/changed skills:
             pip install requires.pip, run selftest(), quarantine failures
        -> repo unchanged?  done, no restart (skill path)
        -> repo changed?    run selftest (imports everything + 89 tests)
             fail: hard reset, report
             pass: commit "self: ...", record last-known-good, restart in place
```

Rollback ladder: "undo that" reverts the last `self:` commit. Crash loop at boot (3 strikes before the first healthy minute) hard-resets to last-known-good before any fragile import runs (`__main__.py` imports supervisor only, first).

### 7. Watchers

Skills with a `watch.interval_secs` field. A 60s background tick runs due watchers; output is spoken only when non-empty AND different from last time. Skipped while a conversation is in flight. Same background loop runs memory consolidation when idle for 30+ minutes: the local model summarizes each unconsolidated day into `memory/DATE.md` and folds durable facts into MEMORY.md.

### 8. Boot

```
python -m jetsonclaw [--headless|--selftest|--doctor]
  boot guard (before other imports)  -> crash loop? revert + re-exec
  load config -> runner -> Jarvis.start():
    whisper load (~5s), piper load + warmup, mic thread, web server, background loop
```

### 9. Deployment (dev machine -> Jetson)

`scripts/deploy.sh` tars tracked files over SSH and commits on the Jetson side (the remote must be a git repo for self-iteration to commit and roll back). `scripts/install.sh` is idempotent: venv, deps, wake models, Piper voice, Claude CLI. `scripts/jetsonclaw.service` for systemd. `--doctor` verifies the lot.

## Events (the contract between core and UIs)

`state, audio_level, wake, transcript, response (partial flag for streamed sentences), agent_start, agent_output, agent_done, skill, error, speaking`

UIs consume events and send back only `say` text. Adding a new surface (another device, a CLI, a bot) means subscribing to the bus or the websocket; the core never knows the difference.

## Prune guide

| If you don't want | Delete | Notes |
|---|---|---|
| Spotify | `skills/spotify.py`, its routing block, `[spotify]` config | nothing else references it |
| The TUI | `tui/` except `blockfont.py`, run with `--headless` | headless printer uses blockfont |
| Block letters | `tui/blockfont.py`, the `block` flag in app/runner/tui | cosmetic only |
| Web dashboard | `server/`, the serve() calls in runner.py | phone access gone |
| Voice output | set `tts.enabled = false` | no code change needed |
| Self-modification | `skills/selfiterate.py`, `supervisor.py`, its routing | also remove boot guard call in `__main__` |
| Watchers | the `watch` parsing in loader + `_run_due_watchers` | skills still work by voice |
| Memory consolidation | `Consolidator` + the idle branch of the background loop | episodic recall still works |
| Episodic memory entirely | `brain/episodic.py`, recall/remember routing | chat loses all context beyond one turn |
| Agent brain entirely | `brain/claude.py`, selfiterate, agent.task routing | becomes a fully local assistant |
```
