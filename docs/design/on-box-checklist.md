# On-box checklist

Steps that can only be run on the powered-on Jetson (Orin Nano 8GB, JetPack r36,
aarch64, Python 3.10). Everything in M0/M1/M2 that carries an ESTIMATE or a
"validate on hardware" note is gathered here. Run top to bottom the next time the
board is on; each item says how to tell pass from fail and what to do on fail.

Setup once per boot:

```bash
ssh abhigya@abhigya-orin
cd ~/remy && git pull
source ~/.remy/venv/bin/activate    # or the project venv
python -m remy --doctor             # baseline: mic/speaker/wake/voice/chat/claude
```

---

## M0 — audio path (the one M0 item that could not be validated off-box)

M0 moved Piper out-of-process (REMY execs the `piper` binary, never imports the
GPL package). The exact CLI flags vary between piper builds, so confirm the
invocation against the installed binary.

1. **A piper binary exists and speaks.**
   ```bash
   which piper
   echo "System online." | piper --model ~/.remy/voices/en_GB-alan-medium.onnx --output-raw \
     | aplay -D default -q -t raw -f S16_LE -r 22050 -c 1
   ```
   - Pass: you hear it.
   - Fail (unknown flag): run `piper --help`; if it uses different flag names,
     set `[tts] binary` and/or adjust `remy/audio/tts.py:piper_cmd` to match, then
     re-test. If no binary at all, install one (apt or a release build).

2. **The sample rate matches the voice.** `read_sample_rate` reads
   `<voice>.onnx.json`; if playback is chipmunk/slow, that companion file is
   missing or wrong — confirm `~/.remy/voices/<voice>.onnx.json` has
   `audio.sample_rate`.

3. **REMY speaks end to end.** Start REMY, say the wake word, ask something, and
   confirm a spoken reply. TTS fails safe (disables, REMY stays up) if the binary
   or voice is missing — so silence means check `--doctor`'s "piper binary" and
   "piper voice" lines.

4. **License guard is clean on-box.**
   ```bash
   python -m remy --doctor | grep -i "piper license"
   ```
   - Pass: `✓ piper license (no in-proc GPL)`.
   - Fail: a GPL `piper-tts` is installed — `pip uninstall piper-tts`. The binary
     is separate and stays.

---

## M1 — Agent SDK engine (the benchmark gate; CLI stays until this passes)

The SDK path is scaffolded and defaults off (`[claude] engine = "cli"`). Do NOT
delete the CLI fallback until all four pass.

1. **Install and self-test with the SDK.**
   ```bash
   pip install -e .[sdk]
   python -m remy --doctor | grep -i "agent engine"   # only shown when engine=sdk
   REMY_CONFIG=... python -m remy --selftest           # or set [claude] engine="sdk"
   ```
   - Pass: doctor shows `✓ agent engine (sdk)`; selftest green; the SDK smoke
     test that skips off-box now runs.

2. **Session RSS + cold-start vs CLI (fills ADR 0001's ESTIMATE).**
   With `engine="sdk"`, run one agent task and sample RSS of the `claude`
   subprocess (e.g. `ps -o rss= -C claude`, or watch `top`), and time first token.
   Repeat with `engine="cli"`. Record both in ADR 0001.
   - Concern: peak must leave headroom under 8GB with qwen resident. If RSS is
     materially worse than the CLI, note it before committing to the SDK.

3. **Resume across a self-restart (the core M1 unlock).**
   Start an agent session under the SDK, capture the `session` line REMY emits,
   restart REMY, then resume that id and confirm the conversation continues.
   - Pass: the resumed session remembers the earlier turns.
   - Fail: the id isn't re-attaching — check `resume=` plumbing before M3 relies
     on it.

4. **Only after 1–3:** flip `engine="sdk"` as default and remove the CLI path in
   a follow-up commit. Until then both engines ship.

---

## M2 — sandbox viability (run this FIRST; it gates the whole approach)

The entire bwrap containment plan (ADR 0003) depends on unprivileged user
namespaces being available on the L4T r36 kernel. This is the single biggest
on-box unknown in the program — check it before building on it.

1. **Unprivileged user namespaces.**
   ```bash
   python -m remy --doctor | grep -i "user namespaces"
   # and directly:
   cat /proc/sys/kernel/unprivileged_userns_clone 2>/dev/null   # 1 = on
   unshare --user --map-root-user echo ok                        # prints ok if allowed
   ```
   - Pass: value is 1 / `unshare` prints ok → bwrap plan is viable.
   - Fail: 0 or permission denied → the kernel needs a config/sysctl change, or
     fall back to landrun (weaker). Do NOT ship the loader sandbox switch until
     this passes; REMY would refuse every script skill.

2. **bwrap present and contains a hostile skill.**
   ```bash
   which bwrap
   python -m remy --doctor | grep -iE "bubblewrap|cgroup"
   ```
   Then the containment acceptance test (once the loader switch lands): a test
   skill that spins (`while True`) and reads `~/.remy/secrets` must time out,
   see nothing, and not block the event loop.
   - Fail (no bwrap): `sudo apt install bubblewrap`.

3. **Then, and only then:** land the loader change that routes script/converse
   skill execution through sandbox profile A and deletes the in-process
   `exec_module` path (`loader.py:69-86,111-120` — today's most dangerous
   behavior). With the sandbox confirmed, the switch is safe; without it, the
   fallback is to refuse the skill with a spoken reason, never run it unsandboxed.

---

## Order

Run **M2 step 1 first** — if unprivileged userns is off, the sandbox milestone
changes shape and it's better to know before anything else. Then M0 audio (so
REMY talks), then the M1 benchmark/resume gate. Record every measured number back
into the ADR that carried it as an ESTIMATE.
