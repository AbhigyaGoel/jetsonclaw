# Prior-Art Landscape Scan

A research and salvage pass over the open-source projects that overlap with
REMY: what to steal, what to avoid, and a PR-ready backlog. This is not a
coding pass; nothing outside `docs/research/` was touched.

- **Run date:** 2026-08-05
- **REMY commit at scan time:** run `git rev-parse --short HEAD`

## At a glance

~90 unique repos verified via `gh api` (target was 80+), 34 deep-dive notes.
Verdict spread:

| Verdict | Count | Headliners |
|---|---|---|
| VENDOR | 8 | smart-turn, whisper_trt, wyoming, aider, mem0, GlaDOS |
| PORT | ~21 | ovos-core, pipecat, livekit/agents, Voyager, dgm, letta |
| DEPEND | ~16 | silero-vad, jetson-containers, go-librespot, bubblewrap, claude-agent-sdk |
| PATTERN-ONLY | ~33 | home-assistant, home-llm, piper1-gpl (GPL), AutoGPT (case study) |
| IGNORE | ~23 | dead, GPU-only, or too heavy for 8GB |

**The three changes to make this month** (argued in `gaps.md`): (1) semantic
end-of-turn via `smart-turn` + `silero-vad`; (2) reconciling memory
consolidation via `mem0`'s update prompt; (3) harden the wake word we already
ship (`openWakeWord` `vad_threshold` + Speex NS). Each is one PR, each fixes a
daily annoyance, none gambles the 8GB budget.

**Sharpest finding:** REMY's self-modification *mechanism* is not novel —
`jennyzzt/dgm` (Darwin Gödel Machine) published it. REMY is novel on
*deployment*: voice-driven, on-device 8GB, no-shell, Claude-Code-billed. Pitch
the deployment, not the mechanism.

## How to read this

| File | What it is |
|---|---|
| `index.md` | Master table, one row per repo, sorted by verdict then relevance. Start here. |
| `deep-dives/<repo>.md` | One note per repo that scored relevance >= 3. Files worth reading, what to lift, what to avoid, license constraint, effort. |
| `gaps.md` | Where REMY lags the field (named), where it is genuinely novel (skeptically), and the three changes to make this month. |
| `backlog.md` | Ranked, actionable items. Top items are each sized to land as one PR. |

## Verdict legend

- **VENDOR** — copy the code into REMY with attribution (permissive license only).
- **PORT** — reimplement the pattern ourselves; do not copy the code.
- **DEPEND** — add as a dependency (a Jetson size/latency cost is recorded).
- **PATTERN-ONLY** — read for ideas; license forbids vendoring (GPL/AGPL/SSPL/CC-BY-NC).
- **IGNORE** — not worth it; the one-line reason is in the table.

## License discipline

REMY is MIT. Every repo's license is recorded. GPL/AGPL/SSPL/CC-BY-NC code is
never proposed for vendoring, only for patterns. MIT/BSD/Apache-2.0 may be
vendored with attribution.

## Refreshing this scan

Metadata (stars, last commit, license, open issues) was captured with:

```bash
gh api repos/OWNER/REPO --jq '{stars:.stargazers_count, pushed:.pushed_at, license:.license.spdx_id, issues:.open_issues_count, archived:.archived}'
```

Citations point at a specific commit SHA and line range so they stay valid as
upstream moves. Re-run the scan when planning a quarter of work, or when a
listed project ships a major release. Repos with no commits in 18+ months were
dropped unless their code was still directly liftable.
