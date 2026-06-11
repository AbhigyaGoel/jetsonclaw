# JetsonClaw

[![CI](https://github.com/AbhigyaGoel/jetsonclaw/actions/workflows/ci.yml/badge.svg)](https://github.com/AbhigyaGoel/jetsonclaw/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)
![Platform](https://img.shields.io/badge/platform-Jetson%20Orin%20%7C%20arm64-76b900)

**JetsonClaw** is a voice assistant that runs on a Jetson Orin Nano and can rewrite its own code. Wake word, speech to text, and chat run fully on device. Anything that needs real work spawns a headless [Claude Code](https://code.claude.com) session billed to your existing Claude subscription, not an API key.

```
» "give yourself a skill to flip a coin"
« "That'll modify my own code. Say yes to proceed."
» "yes"
« "On it. Give me a few minutes."
    agent: Creating a coin flip skill at ~/.jetsonclaw/skills/coinflip/
« "Done. Say 'flip a coin' and I'll respond with Heads or Tails."
» "flip a coin"
« "HEADS!"
```

Real session, unedited. The skill existed before the sentence finished.

## How it works

```
mic > openWakeWord > faster-whisper >  intent router >  skills (Spotify, self-grown)   local, <1s
                                                     >  qwen2.5 via ollama             local chat
                                                     >  Claude Code headless           agent tasks
                                       EventBus      >  TUI / web dashboard / logs
responses > Piper TTS (streamed sentence by sentence)
```

Two brains on purpose. Quick commands never leave the room. Code changes and integrations go to a real agent.

## Quick start

```bash
# on the Jetson (or any arm64 Linux with a mic)
git clone https://github.com/AbhigyaGoel/jetsonclaw ~/jetsonclaw
cd ~/jetsonclaw && bash scripts/install.sh

# local chat model
curl -fsSL https://ollama.com/install.sh | sh && ollama pull qwen2.5:3b

# agent brain auth: run on any machine with a browser, paste token to the Jetson
claude setup-token
echo 'CLAUDE_CODE_OAUTH_TOKEN=<token>' >> ~/.jetsonclaw/env

# check everything, then run
~/.jetsonclaw/venv/bin/python -m jetsonclaw --doctor
~/.jetsonclaw/venv/bin/python -m jetsonclaw
```

Dashboard at `http://<jetson-ip>:8484`. Install it as a PWA on your phone: it has a mic button, so your phone is a remote.

## What it does

| Say | Result |
|---|---|
| "play blinding lights" | Spotify search and play |
| "play my gym playlist" | fuzzy playlist match |
| "what time is it" | a self-grown skill answers |
| "remember that my locker code is 4912" | written to long-term memory |
| "what do you remember about my locker" | recalled from memory |
| "give yourself a weather skill" | writes, tests, and hot-loads a new skill |
| "upgrade yourself to ..." | edits its own repo, gated by tests |
| "undo that" | reverts the last self-change |
| "status report" | uptime, skills, memory, RAM, disk |
| anything else | local chat with conversation memory |

Typed input works everywhere (TUI, dashboard, stdin) and runs the same pipeline as voice.

## Self-modification, safely

1. Every change runs in a fresh Claude Code session inside the repo
2. The change must pass `python3 -m jetsonclaw --selftest` or it is discarded
3. Passing changes are committed; the previous commit is recorded as last known good
4. A crash loop at boot auto-reverts to last known good after 3 failed starts
5. The agent has no shell access by default and asks for a spoken yes before running

Skills are simpler: a `SKILL.md` plus optional `handler.py` under `~/.jetsonclaw/skills/`, hot-loaded on the next utterance with no restart. Declared pip dependencies are installed by the harness, and a failing selftest quarantines the skill. See [docs/skills.md](docs/skills.md).

## Memory

One episodic store, three views: the last few turns feed chat context, keyword search recalls older interactions, and an idle-time consolidation pass summarizes each day and folds durable facts into `MEMORY.md`. Personality lives in `~/.jetsonclaw/SOUL.md` and is plain markdown the agent itself can edit.

## Hardware

- NVIDIA Jetson Orin Nano (8GB), JetPack r36, Ubuntu 22.04
- any USB mic (tested with a Logitech C270 webcam)
- any speaker (HDMI or USB)

Other arm64 or x86 Linux boards should work; the Jetson is what it is tuned and tested on.

## Providers

The chat brain speaks two protocols: ollama (the on-device default) and OpenAI chat completions. One config block covers OpenAI, Groq, OpenRouter, Together, DeepSeek, Mistral, vLLM, llama.cpp, LM Studio, and anything else with a `/v1/chat/completions` endpoint:

```toml
[chat]
provider = "openai"
url = "https://api.groq.com/openai/v1/chat/completions"
model = "llama-3.3-70b-versatile"
api_key_env = "GROQ_API_KEY"
```

## Configuration

Copy [config.example.toml](config.example.toml) to `~/.jetsonclaw/config.toml`. Assistant name, wake word model, voices, models, ports, and agent permissions are all config.

## Docs

| Doc | Covers |
|---|---|
| [docs/features.md](docs/features.md) | everything REMY does, and how to remove what you don't want |
| [docs/skills.md](docs/skills.md) | skill format, synthesis, activation, quarantine |
| [docs/wake-word.md](docs/wake-word.md) | training a custom wake word |
| [docs/jetson.md](docs/jetson.md) | Jetson-specific setup notes and pitfalls |

## Cost

Wake word, STT, TTS, chat, Spotify, and skills run locally and cost nothing. Agent tasks draw from the Agent SDK credit included in Claude subscriptions (about $100/month equivalent on Max 5x as of mid 2026).

## License

MIT
