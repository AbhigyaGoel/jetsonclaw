# Features

What REMY does, how to invoke it, and how to turn it off. Everything here works today.

## Voice

| Feature | How |
|---|---|
| Wake word | say "hey jarvis" (custom models supported, see [wake-word.md](wake-word.md)) |
| Speech to text | on device, whisper base, about 1s |
| Spoken replies | Piper TTS, starts speaking the first sentence while the rest generates |
| Interruption | wake word cuts off ongoing speech |
| Typed input | TUI input box, dashboard input, or stdin; identical behavior to voice |

Turn off voice replies: `tts.enabled = false`. Tune sensitivity: `wake.threshold`.

## Chat

Talks through a local model (ollama by default, or any OpenAI-compatible endpoint via `[chat]` config). Replies use the last few turns, recalled older interactions, and any matching knowledge skills. "Forget that" or "new topic" clears the thread.

## Memory

| Say | Happens |
|---|---|
| "remember that my locker code is 4912" | written to long-term memory instantly |
| "what do you remember about my locker" | answers from long-term facts, daily summaries, and past conversations, with dates |

Unprompted: every interaction is logged, and when REMY has been idle half an hour it consolidates past days into summaries and folds durable facts into long-term memory. Personality and user facts live in `~/.remy/SOUL.md` and `USER.md`, plain markdown you (or REMY) can edit.

## Skills

Folders under `~/.remy/skills/`, hot-loaded on the next utterance. No restart. Four kinds, mixable:

- **voice**: trigger phrases run a shell command or Python handler ("what time is it")
- **watchers**: run on a schedule, speak only when their output changes (CI failed, package shipped)
- **knowledge**: keyword-matched notes injected into chat context (house facts, project context)
- **follow-up**: a skill that just answered gets first refusal on the next utterance, enabling multi-turn flows

Format reference and examples: [skills.md](skills.md), `examples/skills/`.

## Self-modification

| Say | Happens |
|---|---|
| "give yourself a [capability]" | an agent writes a new skill; it exists within minutes, no restart |
| "upgrade yourself to [change]" | the agent edits REMY's own code, gated by the test suite |
| "continue" / "keep going" | resumes the previous agent session with its context |
| "undo that" | reverts the last self-change |

Safety, in order: spoken yes required before any agent runs; the agent has no shell access; new skills get their dependencies installed and selftests run by the harness, failures quarantined; code changes must pass the full test suite, with one repair attempt before rollback; every accepted change is a git commit with a recorded fallback; a crash loop at boot auto-reverts; everything is journaled to `~/.remy/EVOLUTION.md` (what was asked, what changed, which commit).

## Agent tasks

"Edit my portfolio site to ..." and similar run a headless Claude Code session in your configured workdir, billed to your Claude subscription. Point `claude.mcp_config` at an MCP servers file and agent tasks inherit those tools (Notion, calendars, whatever you connect). Optional heartbeat: standing instructions in `~/.remy/HEARTBEAT.md` run on a cadence and stay silent unless something needs you.

## Spotify

Play a track by name, play a playlist by fuzzy match, skip, pause, resume, what's playing. Needs OAuth tokens at `spotify.token_file`; remove the file and the feature disappears.

## Surfaces

- **TUI** on the device: block letters, VU meter, conversation and agent panes, input box
- **Dashboard** at `http://<jetson>:8484`: live state ring, transcript, agent activity, text input, phone mic button, optional phone-side TTS; installable as a PWA. Optional `server.auth_token`
- **Headless**: console output plus stdin, for systemd and scripting

## Operations

- `--doctor`: checks mic, speaker, wake model, voice, chat brain, claude auth, Spotify, with fix commands
- `--selftest`: imports every module and runs the test suite (the same gate self-modification uses)
- "status report": uptime, skills, memory counts, free RAM and disk, last-turn latency
- `scripts/verify_wake.py`: tests any wake model with synthesized audio, no mic needed
- systemd unit, idempotent installer, crash-loop auto-revert

## Removal guide

| Don't want | Do |
|---|---|
| Spotify | delete the token file, or `skills/spotify.py` + its routing block |
| voice replies | `tts.enabled = false` |
| the dashboard | delete `server/`, remove its launch in `runner.py` |
| the TUI | run `--headless` |
| self-modification | delete `skills/selfiterate.py` + `supervisor.py` + their routing |
| watchers / heartbeat | don't create watch skills / leave `heartbeat_hours` at 0 |
| memory consolidation | delete `Consolidator` + its branch of the background loop |
| all cloud agents | delete `brain/claude.py` and agent routing; fully local from then on |
