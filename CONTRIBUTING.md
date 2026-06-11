# Contributing

## Ground rules

- `python -m jetsonclaw --selftest` and `ruff check jetsonclaw tests` must pass. CI enforces both.
- Keep it lean. This project deletes code enthusiastically; a PR that removes lines is as welcome as one that adds them.
- For features, open an issue first. Bug fixes can go straight to PR.
- Say what hardware you tested on (Jetson model and JetPack version, or "x86 Linux, no audio").

## AI disclosure

AI-assisted PRs are welcome. State the tier in your PR description:

1. mostly human
2. AI-assisted, human reviewed line by line
3. mostly AI-generated

For tiers 2 and 3, you must be able to explain every line. PRs where the submitter clearly has not read their own diff get closed without review.

## Skills

New example skills go in `examples/skills/` with a `SKILL.md` and, for script skills, a `selftest()` in the handler. Skills that need API keys must read them from a `config.yaml` beside the handler and fail with a clear instruction when missing.
