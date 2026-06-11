# JetsonClaw

**JARVIS on a Jetson.** A voice-activated AI assistant that runs on a $249
Jetson Orin Nano, talks back like a butler, controls your Spotify — and
**rewrites its own code when you ask it to.**

> *"Hey Jarvis — give yourself a weather skill."*
> *(two minutes later, after editing its own repo, testing itself, and restarting)*
> *"Done and tested, sir."*

## How it works

```
mic ─ openWakeWord ─ faster-whisper ─┬─ intent router ──┬─ skills (Spotify, …)      fast, local, <1s
                                     │                  ├─ qwen2.5 via ollama        chat, local
                                     │                  └─ Claude Code (headless)    agent tasks
                                     ▼
                          EventBus ──┬── Textual TUI (on-device)
                                     └── web dashboard PWA (any phone/PC on LAN)
            Piper TTS ◄── responses
```

Two brains, deliberately:

- **Local fast path** — wake word, speech-to-text, intent matching, Spotify, and
  chat all run on-device. Quick commands never leave the room.
- **Agentic path** — anything that needs real work ("edit my portfolio site…",
  "upgrade yourself…") spawns a headless [Claude Code](https://code.claude.com)
  session, authenticated with your existing Claude subscription via
  `claude setup-token`. **No per-token API billing.**

## Self-iteration (the fun part)

When you say *"Jarvis, upgrade yourself to …"*:

1. snapshot the current git HEAD
2. a Claude Code session edits JetsonClaw's own repo
3. the change must pass `python3 -m jetsonclaw --selftest` (imports every
   module + runs the test suite) — failures are discarded automatically
4. passing changes are committed, the previous commit is recorded as
   **last-known-good**, and JARVIS restarts itself with the new code
5. *"Jarvis, undo that"* reverts the last self-made commit
6. if a change somehow crashes the assistant at boot, a crash-loop guard
   auto-reverts to last-known-good after 3 failed starts

## Hardware

- NVIDIA Jetson Orin Nano (8GB) — JetPack r36 / Ubuntu 22.04
- any USB mic (tested: Logitech C270 webcam mic)
- any speaker (HDMI monitor audio or USB)

## Install

```bash
# on the Jetson
git clone https://github.com/you/jetsonclaw ~/jetsonclaw
cd ~/jetsonclaw && bash scripts/install.sh

# ollama (local chat brain)
curl -fsSL https://ollama.com/install.sh | sh && ollama pull qwen2.5:3b

# Claude auth: on any machine with a browser
claude setup-token        # then on the Jetson:
echo 'CLAUDE_CODE_OAUTH_TOKEN=<token>' >> ~/.jetsonclaw/env   # for the systemd service
echo 'export CLAUDE_CODE_OAUTH_TOKEN=<token>' >> ~/.bashrc    # for terminal runs
```

Run it:

```bash
~/.jetsonclaw/venv/bin/python -m jetsonclaw            # TUI
~/.jetsonclaw/venv/bin/python -m jetsonclaw --headless # console / systemd
```

Dashboard: `http://<jetson-ip>:8484` — add to home screen on your phone, it's a PWA.

## Voice commands

| say | happens |
|---|---|
| "hey jarvis, play blinding lights" | searches Spotify, plays it |
| "play my gym playlist" | fuzzy-matches your playlists |
| "skip" / "pause" / "what's playing" | playback control |
| "what time is it" | a **self-grown skill** (see below) |
| "upgrade yourself to ..." | self-iteration (see above) |
| "undo that" | reverts the last self-change |
| "edit the portfolio site to ..." | agent task in your configured workdir |
| "forget that" / "new topic" | clears conversation memory |
| anything else | local LLM chat — with conversation memory, streamed into TTS sentence-by-sentence |

Agent tasks ask for a spoken **"yes"** before running (configurable), and the
agent runs **without shell access by default** — a misheard command can edit
files in its workdir but never execute arbitrary bash.

No mic handy? Every surface accepts typed commands through the *same*
pipeline: the TUI input box, the dashboard input, or plain stdin in
`--headless` mode (`echo "what time is it" | python -m jetsonclaw --headless`).

## Self-grown skills

Skills are directories under `~/.jetsonclaw/skills/` with a `SKILL.md`:

```markdown
---
name: weather
description: current weather
triggers: ["weather", "is it raining"]
action:
  command: curl -s "wttr.in/?format=%C+%t"
requires:
  bins: [curl]
---
```

They **hot-load on the next utterance** — no restart, no redeploy. Which means
when you say *"Jarvis, give yourself a weather skill"*, the agent writes one of
these files and the capability exists by the time it finishes talking. Skills
are plain files: share them, version them, copy them between machines.

## Personality is data, not code

`~/.jetsonclaw/` holds `SOUL.md` (persona), `USER.md` (you), `MEMORY.md`
(long-term facts) — injected into every brain call, editable by you *or by
JARVIS itself*. "Jarvis, be 20% more sarcastic" is a file edit, not a PR.

## Hard-won Jetson lessons baked in

- openWakeWord scores ~0 on float32 audio — must be **int16** (this cost a day)
- PyAudio device indices are unstable on Jetson — mic capture is `arecord` only
- numpy must stay **<2** (tflite-runtime segfaults on 2.x)
- pip ctranslate2 has no CUDA on aarch64 — Whisper runs CPU int8, still real-time

## Subscription budget note

Headless `claude -p` usage draws from your plan's Agent SDK credit
(Max 5x ≈ $100/mo equivalent as of June 2026). Fast-path commands never touch
it — only agent tasks and self-iteration do.

## License

MIT
