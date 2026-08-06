# Blind-Spot Scan — 2026-08-06

The 2026-08-05 scan was seeded with voice-assistant repos, so five areas that the
capability program depends on got zero coverage: MCP, browser control, vision,
job orchestration, and secrets/OAuth. This pass fills them to the same standard
(verified via `gh api`, cited to `repo@sha:path:Lx-y`, licensed, costed against
8GB) and re-examines claude-agent-sdk-python and bubblewrap under the new
thesis: REMY as an autonomous agent that happens to have a voice.

~40 additional repos examined, ~30 new or rewritten deep-dives. New rows are in
`index.md` under "Blind-spot additions".

## The four ceilings, verified against source

The program brief named four structural ceilings. All four are real. Three need
corrections, stated here in writing as requested.

**1. Shell — confirmed, and understated.** `remy/skills/loader.py:95-109` runs
`action.command` via `subprocess.run(["bash", "-c", cmd])` with a trimmed PATH
(cosmetic, not a boundary), 30s timeout, no sandbox. The brief missed the worse
hole: `loader.py:111-120` (`_run_script`) and `loader.py:69-86` (`converse`)
import and exec a skill's `handler.py` **in the main REMY process** — no
timeout, no isolation, full access to REMY's state, and a `while True` in a
synthesized skill blocks the event loop from a worker thread REMY never
reclaims. Containment must fix in-process script skills, not just the bash
path.

**2. Job lifetime — confirmed, one correction.** The 600s figure
(`config.py:84`) is applied per stdout line read (`brain/claude.py:71-72`), so
it is an inactivity timeout, not wall clock — a chatty agent session can
already run for hours. The real ceiling is exactly what the brief said
otherwise: `_route_lock` (`app.py:53`, held for the entire `_route` in
`app.py:196-199`) serializes everything, the background loop refuses to run
while it is held (`app.py:103-104`), resume is `--continue` most-recent-only
(`claude.py:43-44`), and nothing survives REMY's own restart — which
self-modification triggers routinely. Detached, resumable, observable jobs are
the requirement.

**3. Credentials — confirmed.** One integration (Spotify, hand-rolled token
JSON, `config.py:99-100`); `claude.mcp_config` plumbed and defaulted empty
(`config.py:91`, wired at `claude.py:45-46`). New urgency from this scan:
Spotify hard-banned `localhost` and LAN-IP redirect URIs in 2025 — the
existing token flow is likely already broken for re-auth (see the secrets
findings below).

**4. Sight — confirmed, one correction.** There is no capture path anywhere in
the tree. But ingestion already exists: the agent's allowed tools include
`Read`, and Claude Code's Read ingests PNG/JPG natively. The gap is producing
images (camera frame, rendered-HTML screenshot), not seeing them. That shrinks
the milestone: sight is a ~10-line `v4l2-ctl` wrapper plus a headless-chromium
screenshot path, not a vision subsystem.

## Findings by area

### MCP ecosystem

The `--mcp-config` hook REMY already plumbs is sufficient for runtime tool
acquisition as-is. Verified from current Claude Code docs (not memory):

- Config is a JSON file of `mcpServers`; each `claude -p` spawn is a fresh
  process that reads it at startup. **A synthesized skill can add a tool by
  writing JSON and respawning — no CLI changes, no trust prompts**, provided
  REMY also passes `--strict-mcp-config` (ignores project `.mcp.json` and its
  interactive approval gate, making every spawn hermetic).
- Tool naming is `mcp__<server>__<tool>`; `--allowedTools mcp__<server>`
  allowlists a whole server. REMY appends server names next to the existing
  static list.
- `--permission-prompt-tool <mcp tool>` can delegate permission decisions to an
  MCP tool — meaning REMY itself can adjudicate dangerous calls by voice once
  it exposes its own server.
- Healthy servers: `github/github-mcp-server` (official, MIT, prebuilt
  linux-arm64 binary, PAT or device-code auth),
  `taylorwilsdon/google_workspace_mcp` (MIT, one Python stdio server for
  Gmail+Calendar+Drive, OAuth callback URI configurable to the Jetson's LAN
  address — the only healthy Gmail path; GongRzhe's Gmail server is archived),
  `modelcontextprotocol/servers` filesystem reference,
  `microsoft/playwright-mcp` for the browser.
- `modelcontextprotocol/python-sdk` (MIT): REMY exposing its own
  speak/notify/memory/capture tools as a stdio server is ~30 lines. This
  inverts the integration — the agent gets hands into REMY.
- RAM (all ESTIMATE, all on-demand per-spawn, zero resident): gh server
  25-50MB, node servers 50-90MB, workspace-mcp 120-200MB, playwright+chromium
  400-700MB.

### Browser and computer control on arm64

- **Playwright's arm64 story is official and verified**: the build registry
  maps `ubuntu22.04-arm64` to CDN chromium and chromium-headless-shell builds
  (HEAD-checked, 205MB/115MB compressed). Ubuntu's own `chromium-browser` is a
  snap stub — avoid it; Playwright's CDN build sidesteps snap.
- **playwright-mcp is the single browser capability**: navigate, click, fill,
  evaluate, accessibility snapshot (token-cheap, no vision needed),
  screenshot, `--storage-state`/`--user-data-dir` for persistent auth.
  Standardize on headless-shell; budget ~300-400MB transient RAM (ESTIMATE),
  which means unloading the ollama model first on 8GB.
- browser-use is PATTERN-ONLY twice over: its own LLM loop needs API-key
  billing (violates the subscription constraint) and it requires Python 3.11.
  The anti-bot CDP ecosystem (nodriver/zendriver) is AGPL — never importable.
- HTML-to-PNG: wkhtmltoimage is archived, WeasyPrint dropped PNG output. The
  render path for the variants demo is playwright's screenshot (or bare
  `chrome-headless-shell --headless --screenshot` with zero tokens).
- TikTok demo reality: favorites are private. The viable paths a runtime agent
  can discover are (1) TikTok's "Download your data" JSON export (includes
  Favorite Videos with links; takes hours-to-days to arrive, so the flow is
  request-now-index-when-ready) and (2) an authenticated playwright-mcp crawl
  as fallback; `yt-dlp` (Unlicense) then batch-fetches metadata per URL.

### Vision

- The variants demo needs **zero new ML**: render PNGs, capture JPEGs, let the
  running Claude session Read them. Cold cost is session spawn 5-10s +
  inference (ESTIMATE); fine for user-initiated one-shots.
- Leanest capture, zero resident: `v4l2-ctl --stream-mmap --stream-skip=5
  --stream-count=1 --stream-to=/tmp/frame.jpg` (UVC MJPEG frames are valid
  JPEGs; the skip discards auto-exposure warm-up).
- Local VLM only when continuous/offline vision is actually scheduled — and
  then it is `ollama pull moondream` (1.7GB, transient via `keep_alive:0`),
  nothing bigger: 3B-class VLMs on this board post 0.5-1.1 tok/s in published
  benchmarks. Wake-on-vision, if ever, is frigate's ~80-line motion gate (MIT,
  pattern port) in front of moondream. Every NVIDIA-branded option (nanoowl,
  jetson-inference, DeepStream) fails the RAM-for-value test.
- OCR: RapidOCR (Apache-2.0, onnxruntime, numpy<2 compatible) only for
  offline/verbatim needs; default document reading is Claude's Read.
- Tripwire: if OpenCV ever enters the repo, pin
  `opencv-python-headless==4.11.0.86` — later wheels require numpy>=2, which
  bricks tflite-runtime.

### Job orchestration

- **claude-agent-sdk-python answers every job-model question** (verified at
  source, citations in the rewritten deep-dive): resume by session ID after a
  REMY restart (`--resume`, vs `--continue` most-recent-only), send follow-up
  messages into a live session, `interrupt()`, `can_use_tool` async callback
  for per-call gating (voice-confirm), in-process Python hooks (PreToolUse
  etc.) that map directly onto the EventBus, in-process MCP servers via
  `@tool` (no separate process), subscription OAuth flows through untouched,
  Python 3.10 OK, and the aarch64 wheel bundles the CLI binary. This removes
  every reason `brain/claude.py` hand-rolls subprocess management.
- **No job-queue library earns a dependency.** huey deletes the queue row
  before running the task (no crash recovery); APScheduler persists schedules,
  not running-job state; arq/rq need redis. The right store is a ~150-line
  sqlite job table REMY owns — jobs as rows with a state machine, stealing
  litequeue's claim/CAS idiom and persist-queue's boot-sweep idea (pid-gated,
  never unconditional).
- **Detachment layer: `systemd-run --user` transient units.** A job unit is a
  child of the user manager, not REMY, so it survives REMY's self-restart;
  `RuntimeMaxSec` gives true wall-clock kill; journald captures logs;
  `systemctl --user stop remy-job-X` is cancellation. Requires
  `loginctl enable-linger` once. Progress and re-attach go through per-job
  files, not IPC: `~/.remy/jobs/<id>/events.jsonl` (OpenHands pattern) plus a
  heartbeat file a watchdog sweeps. The complete crash-recovery state is one
  row: `{session_id, unit_name, cwd, state, heartbeat_ts}`.

### Secrets and OAuth

- **Google device flow cannot do Calendar or Gmail** — its scope allowlist is
  email/profile/drive.file-class only (doc-verified). Any Google capability
  requires a browser-completed loopback flow, and loopback redirect URIs must
  be 127.0.0.1 (LAN IPs not registerable for native clients). There is no
  fully-by-voice Google flow; the workable pattern is voice-guided phone flow
  with one copy-paste, or the taylorwilsdon workspace-mcp server's LAN
  callback (it acts as the redirect host itself). Also: an OAuth client left
  in "Testing" status gets 7-day refresh tokens — the onboarding doc must
  walk the owner through creating their own client and setting it to "In
  production (unverified)".
- **GitHub is the easy one**: device flow with a speakable 8-character code,
  or just depend on `gh` (MIT), which already stores tokens and hands them
  out via `gh auth token`. First credential the broker should support — it
  proves the voice loop cheaply.
- **Spotify changed the rules in 2025**: HTTPS required except literal
  `http://127.0.0.1`; `localhost` and LAN IPs banned. REMY's hand-rolled token
  flow needs a migration regardless of this program.
- **Threat model called honestly**: single-user device; adversary #1 is REMY's
  own synthesized skills and agent sessions exfiltrating secrets via
  prompt/log/git, not other local users. Store accordingly: `~/.remy/secrets/`
  (0700, outside the repo), age-encrypted per credential (BSD-3), broker
  process is the only decryptor. Rejected: keyring/SecretService (headless
  dbus+unlock trap), systemd-creds (needs systemd 250; Jetson has 249), TPM
  (Orin fTPM requires fused secure boot; impractical — noted and moved on).
- **Broker pattern (aws-vault's shape)**: skills declare
  `requires.credential: <provider>`; at spawn the broker injects a
  `127.0.0.1:<port>` URL plus a per-invocation bearer token; the skill fetches
  a short-lived access token on demand; the refresh token never leaves the
  broker. Missing credential raises a grant-needed event that triggers the
  voice+phone walk-through.
- **Available today, one line**: Claude Code `permissions.deny` supports
  `"Read(~/.remy/secrets/**)"` — deny rules beat allow rules. Plus env-scrub
  before spawning agent sessions, and a redaction filter (regex for `ya29.`,
  `gho_`, `refresh_token`, `AIza`) on episodic memory and event-bus writes,
  since REMY self-commits and logs everything.

### Containment

- **One primary mechanism: bubblewrap** (apt `bubblewrap 0.6.1` on jammy
  arm64, LGPL — exec boundary, fine). Three frozen profiles, each wrapped in
  a `systemd-run --user --scope` for memory/pids/wall-clock caps: (A) skill
  run — tmpfs root, only the skill dir bound, optional network, 512M/30s; (B)
  pip into a dedicated venv — network, writes only the venv, 1G/600s; (C)
  toolchain job — a `systemd-run --user` transient unit with
  `PrivateUsers=yes ProtectHome=tmpfs BindPaths=<job dir>`, 3G/RuntimeMaxSec.
  Exact command lines are in the bubblewrap deep-dive.
- **Agent shell is not a REMY invention**: Claude Code ships its own sandbox
  (`anthropic-experimental/sandbox-runtime`: bwrap + socat + a domain-filtering
  proxy, arm64 supported). Enabling it inside profile-C units gets
  per-domain network egress control that raw bwrap cannot express
  (`--unshare-net` is all-or-nothing).
- **In-process `action.script` must die**; there is no in-process Python
  sandbox (RestrictedPython disclaims itself). Script skills move to
  subprocess-under-profile-A; if latency hurts, OVOS's persistent
  one-skill-per-process worker (`ovos-skill-launcher`) is the pattern.
- Verdict roll: nsjail IGNORE (unpackaged, build fight), firejail IGNORE
  (SUID binary is an attack-surface increase), gVisor/microVMs IGNORE (KVM
  not in stock L4T kernels; syscall tax), podman IGNORE for per-skill use
  (image weight, cold start), landrun conditional (kernel 5.15 = Landlock ABI
  v1 FS-only, and L4T may not enable it at all).
- **Self-mod jobs still get sandboxed** — not to prevent self-modification but
  to bound blast radius: agent works in a disposable git worktree with
  `~/.remy` hidden; commit/selftest/restart gating stays with the trusted
  harness outside the sandbox.

## The single points of failure to verify on-box (Jetson is off; all deferred)

1. `unshare -Ur true` — unprivileged user namespaces on the L4T r36 kernel.
   Everything above assumes this passes; fallback (landrun) is much weaker.
   Put it in `--doctor` and selftest.
2. `grep landlock /sys/kernel/security/lsm` — gates the bonus layer only.
3. cgroup v2 + controller delegation (`MemoryMax`/`TasksMax` in --user mode;
   `CPUQuota` likely a no-op on systemd 249 — verify, don't assume).
4. RAM/latency figures marked ESTIMATE throughout — benchmark
   headless-shell, workspace-mcp, and SDK session RSS on the box before
   trusting the choreography.
5. `loginctl enable-linger` for job units surviving logout.

## What this changes about the plan

1. **Adopt the Agent SDK; delete `brain/claude.py`'s hand-rolled subprocess
   handling.** Sessions get resume-by-ID, mid-session input, interrupts,
   per-call permission gating, and hook-based progress events — all things the
   plan needs and the CLI wrapper cannot give.
2. **Jobs leave REMY's process.** A detached job is a `systemd-run --user`
   transient unit running a small SDK-based runner; REMY keeps a sqlite job
   table and tails per-job event files. This breaks ceiling 2 without making
   REMY a distributed system.
3. **Capability acquisition is a config write.** New tool = write mcp-config
   JSON + append `mcp__<name>` to allowedTools + spawn (always with
   `--strict-mcp-config`). The mechanism the thesis needs already exists; what
   REMY lacks is the registry, the broker, and the discipline around it.
4. **REMY becomes an MCP server too** — speak/notify/memory/capture exposed to
   its own agent sessions, and later `--permission-prompt-tool` routes
   permission decisions through REMY's voice.
5. **Containment stack is bwrap (3 profiles) + Claude Code's own sandbox for
   agent Bash + systemd caps** — and giving the agent Bash becomes acceptable
   the moment those land together.
6. **The credential broker is a prerequisite for demos 1-4**, and GitHub
   device flow is the cheapest first proof. Google requires an owner-provisioned
   OAuth client and a phone; say so in onboarding rather than pretending
   voice-only works.
7. **Sight is two small capture paths** (v4l2 one-shot, headless-shell
   screenshot), not a vision subsystem. Local VLM deferred until a
   continuous-vision feature exists.
8. **Two pre-existing items got more urgent**: the in-process `piper1-gpl`
   import (live GPL violation, unchanged) and the Spotify redirect-URI
   migration (provider policy already changed under it).
