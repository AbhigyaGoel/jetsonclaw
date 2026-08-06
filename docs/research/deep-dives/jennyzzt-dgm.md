# jennyzzt/dgm — PORT (closest analog; be skeptical)

Sakana's Darwin Gödel Machine. A coding agent that **iteratively rewrites its
own codebase** and empirically validates each change on SWE-bench/Polyglot,
keeping an **archive of all validated versions** (evolutionary lineage) and
choosing parents by score. This is REMY's pitch — done first, with a paper
(arXiv:2505.22954).

- **Stars/health:** 2.2k, active (2025-08) · **License:** Apache-2.0
  (vendorable)

## Does better than REMY
- **Archive/lineage, not a single last-known-good.** REMY records ONE
  last-known-good; DGM keeps a full archive and can branch from any prior
  validated commit.
- **Empirical benchmark validation, not just a smoke selftest.** REMY gates on
  `--selftest` (pass/fail). DGM gates on a measured accuracy delta — "actually
  improved," not just "didn't crash."

## Read these files
- `jennyzzt/dgm@a565fd2:utils/evo_utils.py:L96-127` — `is_compiled_self_improve`,
  the acceptance gate: requires perf keys present, at least one non-empty patch,
  and all issues actually evaluated. Steal the "did the change even run on all
  checks" guard and the empty-patch (no-op) rejection.
- `self_improve_step.py:L400-419` — two-stage gate: `is_compiled_self_improve`
  then `diagnose_improvement` only if compiled.
- `DGM_outer.py:L50-109` — `choose_selfimproves` picks parents from the archive
  by `accuracy_score` + child-count; `:L15-35` persists the archive metadata.

## Lift
The two-stage gate (selftest → improvement diagnosis) and the archive-of-
validated-commits with parent selection. Even keeping a *list* of
last-known-good commits (not one) is a cheap, high-value steal.

## Avoid
DGM runs untrusted model code in Docker and explicitly warns about destructive
behavior. REMY's "agent has NO shell" is *stronger* isolation — this is REMY's
advantage, not a gap.

## License constraint
Apache-2.0 — vendorable with attribution.

## Effort
**M** — archive + parent-selection is liftable; the SWE-bench harness is not
needed. **Skeptic's note:** DGM beat REMY to the core mechanism; position REMY
on deployment (voice/on-device/no-shell), not on self-verifying self-mod.
