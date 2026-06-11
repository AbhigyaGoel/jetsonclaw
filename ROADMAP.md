# Roadmap

Five pillars, no dates. Comment on a matching issue or open a PR; for anything large, open an issue first.

## Voice

- custom wake word models documented end to end (training guide exists, smoothing the path)
- barge-in: interrupt the assistant mid-sentence (needs echo cancellation)
- better VAD than RMS thresholds (silero-vad, onnx)

## Self-modification

- property-based fuzzing of the intent parser, agent-authored
- CHANGELOG.md maintained by the assistant itself: what it changed and why
- spec-first changes: the agent writes failing tests before implementing

## Skills

- more in-repo examples (see examples/skills/)
- richer watcher patterns: calendars, mailboxes, RSS
- skill sharing without a registry: a curated list in this repo

## Memory

- temporal queries ("what did I ask last Tuesday") answered from daily summaries
- behavioral calibration: thanks/corrections drift SOUL.md over time

## Hardware

- verified setup guides for Raspberry Pi 5 and generic x86 Linux (everything already runs on CPU)
- measured latency and RAM tables per board
- multi-device presence: satellite mics/speakers on the LAN sharing one brain

## Explicitly out of scope

- chat channel integrations (WhatsApp, Telegram, ...): OpenClaw and PicoClaw do this well already
- a skill registry: ClawHub exists
- timers and alarms: your phone is better at this
