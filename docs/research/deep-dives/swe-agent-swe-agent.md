# SWE-agent/SWE-agent — PORT

SWE-bench-winning agent. Runs the agent in an isolated runtime (SWE-ReX),
produces a **git patch as the unit of change**, and only auto-applies it if it
looks promising.

- **Stars/health:** 20.0k, active (2026-08) · **License:** MIT (vendorable)

## Does better than REMY
Treats the change as a *patch artifact* that can be saved, inspected, and applied
with `git apply` separately from generation — cleaner than editing in place — and
adds an "is this patch worth applying" gate before touching the repo.

## Read these files
- `SWE-agent/SWE-agent@3ea751c:sweagent/run/hooks/apply_patch.py:L36-92` —
  `SaveApplyPatchHook`: saves the patch to a per-instance dir, gates local
  application behind `_is_promising_patch(result.info)`, then `git apply`.
- `sweagent/utils/patch_formatter.py`, `sweagent/environment/swe_env.py` — the
  env-isolation + patch-formatting boundary.

## Lift
Patch-as-saved-artifact before apply; a `_is_promising_patch`-style pre-apply
gate. REMY should gate its `git commit` behind an equivalent check (its selftest
*is* that check) and keep the patch as an artifact for the EVOLUTION.md journal.

## Avoid
Adopting SWE-ReX sandboxing wholesale — heavier than REMY's no-shell model needs
(use bubblewrap instead).

## License constraint
MIT — vendorable with attribution.

## Effort
**S** for the pattern (save patch → gate → apply); **L** for full SWE-ReX.
