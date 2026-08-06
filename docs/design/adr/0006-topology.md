# ADR 0006: Stay single-box; design for a satellite split, do not build it

Status: proposed
Date: 2026-08-06

## Context

REMY is one asyncio process on one Jetson Orin Nano 8GB, with faster-whisper,
ollama qwen2.5:3b, piper, and openWakeWord resident (roughly 3-4GB). The new
capabilities add transient RAM spikes: a browser task wants 400-700MB, a local
VLM (if ever admitted) 2GB-plus. The program brief lists "whether REMY splits
into satellite/server" as an irreversible decision to make.

A split (mic/wake/TTS on a small satellite, models and agent on a server) is the
standard answer to RAM pressure - it is exactly what `rhasspy/wyoming-satellite`
and the Home Assistant Voice architecture do. But it doubles the operational
surface (two boxes, a network protocol, failure modes when the link drops) for a
system whose entire selling point is being one self-contained box the owner
talks to.

## Decision

Stay single-box for the entire capability program. Do not build a satellite
split. But make the two decisions that keep it cheap later:

- Keep the EventBus the sole spine (`events.py`) and keep every surface a
  subscriber, so a network transport can be added as just another subscriber/
  publisher without touching producers.
- When a job or browser task needs more RAM than is free, solve it by
  transient model unload (ollama `keep_alive` / unload, the existing mechanism)
  and by running the heavy task in a systemd-run unit (ADR 0002) that exits and
  frees its RAM - not by adding a second machine.

Revisit the split only if a genuinely resident second model (a persistent local
VLM for continuous vision) becomes a hard requirement that cannot coexist with
qwen on 8GB. That is a future feature, not part of this program.

## Rationale

- The RAM spikes this program introduces are transient (a browser task, a pip
  install, a toolchain job), and transient spikes are handled by unload-and-run,
  which REMY already has the primitive for. None of them justify a second box.
- The one thing that would justify a split - a resident VLM - is explicitly
  deferred (ADR 0008). Deciding to split now would be building for a feature we
  have decided not to build.
- Keeping the EventBus as the seam means the split stays a small change if it is
  ever needed, so deferring costs almost nothing.

## Alternatives rejected

- Build the satellite/server split now. Rejected: doubles ops surface for RAM
  pressure that is transient and otherwise solvable; contradicts the
  self-contained-box premise.
- Offload models to a cloud endpoint. Rejected: breaks the on-device,
  subscription-billed, works-without-internet-for-the-core-loop premise.

## Consequences

- The "memory-pressure model supervisor" (the novel item in
  `docs/research/backlog.md`) becomes load-bearing: transient unload is the
  chosen answer to RAM pressure, so REMY needs a priority-based unload policy
  under pressure. This program depends on it for browser and VLM tasks.
- No wyoming/satellite code is written now; the wyoming envelope stays a
  future-proofing note, not a milestone.

## Verify on-box

- Peak RAM during a browser task with qwen unloaded stays within 8GB (ESTIMATE
  now; measure).
- ollama unload/reload latency around a browser task is tolerable for the demo.
