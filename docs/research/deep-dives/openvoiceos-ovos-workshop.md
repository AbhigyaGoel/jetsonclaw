# OpenVoiceOS/ovos-workshop — PORT

The OVOS skill SDK: an `OVOSSkill` base class, `@intent_handler`/
`@fallback_handler`/`@common_query` decorators, and a `SkillLoader` that
hot-loads/reloads skill modules with a filesystem watcher. The mature analog to
REMY's SKILL.md + handler.py.

- **Stars/health:** 6 stars but active (2026-08) · **License:** Apache-2.0
  (portable)

## Does better than REMY
- A **clean reload** path: `remove_submodule_refs()` deletes `sys.modules`
  entries so a reloaded skill fully re-imports. REMY's mtime-based script-skill
  reload almost certainly leaks stale submodule refs (a real latent bug).
- **Event-driven reload** via inotify instead of per-utterance mtime polling.
- **`reload_allowed`** gating and a clean `_unload()` (stops watchers, emits
  shutdown) — a lifecycle REMY's quarantine could reuse.
- A decorator taxonomy (`@intent_handler`, `@fallback_handler(priority)`,
  `@common_query`, `@converse_handler`) that's a menu of skill-capability types.

## Read these files
- `OpenVoiceOS/ovos-workshop@7aaa4c5:ovos_workshop/skill_launcher.py:L34-40` —
  `remove_submodule_refs()`; `:L236-271` — `load_skill_module`/`get_skill_class`,
  `reload()` gated by `reload_allowed`, watchdog shut down on unload.
- `ovos_workshop/decorators/__init__.py:L57-166` — the decorator family.

## Lift
The `remove_submodule_refs` clean-reload trick + reload-permission gating; the
decorator taxonomy as a design reference.

## Avoid
The messagebus coupling and `RuntimeRequirements` internals.

## License constraint
Apache-2.0 — portable with attribution.

## Effort
**S** (the reload-hardening fix is ~1 file) / **M** (inotify watcher + decorators).
