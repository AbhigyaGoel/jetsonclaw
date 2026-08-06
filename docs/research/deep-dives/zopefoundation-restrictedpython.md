# zopefoundation/RestrictedPython — IGNORE (in-process Python sandboxing is not a thing; move scripts out of process)

The Zope-era compiler that rewrites a Python subset (guarded getattr, no bare
import, print collection) so plugin code runs in a "trusted environment". It
is the best-known attempt at in-process Python restriction, and its own README
disclaims sandbox status. For REMY's in-process `action.script` hole the
honest engineering answer is: there is no in-process fix; the fix is running
`handler.py` as a subprocess under bwrap profile A.

- **Stars/health:** 735, active (2026-07) · **License:** ZPL-2.1 (permissive,
  MIT-compatible; NOASSERTION on GitHub)

## Does better than REMY
Nothing REMY should keep in-process. Against a hostile LLM-synthesized script
it is bypassable (CPython gives too many object-graph paths to `__builtins__`
/ frames / gc); against ACCIDENTS it only prevents imports and attribute
tricks, while REMY's actual accident classes (blocking the event loop with
`time.sleep`, infinite loops, memory balloons, clobbering REMY state) are
untouched: RestrictedPython has no preemption, no timeouts, no resource caps.

## Read these files
- `zopefoundation/RestrictedPython@61f1849:README.rst:L25-30` — "RestrictedPython
  is not a sandbox system or a secured environment"; CPython-only.

## Lift
None. Prior art for the replacement instead: OVOS runs every skill as a thread
in one skills process by default, but ovos-workshop ships a per-skill process
container (`ovos-skill-launcher`): a `SkillContainer` connects to the message
bus, loads one skill, and stays resident, i.e. a persistent worker process per
skill rather than per-invocation spawn
(`OpenVoiceOS/ovos-workshop@7aaa4c5:ovos_workshop/skill_launcher.py:L558-571`
and `L617-652`). REMY's equivalent: spawn `python3 handler.py` under profile A
per invocation first (simple, ~0.3-1s startup **ESTIMATE** on Orin); if
latency hurts for hot skills, graduate to a persistent bwrapped worker holding
the skill module, fed requests over stdin JSON, killed/respawned on timeout.

## Avoid
Any design where synthesized Python shares the REMY process: no exec/import
of skill code in-process, even "restricted". Also skip audit-hook/`sys.
settrace` schemes; same fatal model.

## License constraint
ZPL-2.1 (moot; not adopted).

## Effort
n/a — effort belongs to the out-of-process runner (bubblewrap dive).
