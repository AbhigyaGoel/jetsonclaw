# anthropics/skills — PORT (align our frontmatter as a superset)

The canonical Agent Skills spec. A skill = a directory with `SKILL.md`
(YAML frontmatter + Markdown body) plus optional `scripts/`, `references/`,
`assets/`.

- **Stars/health:** 166k, active (2026-07) · **License:** Apache-2.0 (spec +
  most skills vendorable; the bundled doc skills are source-available, pattern-only)

## Does better than REMY
A formal, versioned frontmatter contract with validation tooling
(`skills-ref validate`) and **progressive disclosure**: name+description (~100
tokens) at startup → full body (<5k tokens) on activation → bundled files on
demand. REMY loads the whole SKILL.md per utterance, wasting context on an 8GB
device.

## Read these files
- `anthropics/skills@b29e7cf:template/SKILL.md` — the canonical minimal skill is
  only `name` + `description`. REMY's frontmatter is a strict superset.
- agentskills.io/specification (spec target) — frontmatter rules: required
  `name` (<=64ch, `[a-z0-9-]`, no leading/trailing/consecutive hyphen, **must
  match dir name**), `description` (<=1024ch); optional `license`,
  `compatibility` (<=500ch, e.g. "requires git, docker, Python 3.14+"),
  `metadata` (str→str map), `allowed-tools`.

## Compatibility verdict
REMY is **structurally compatible but field-divergent**. `requires.pip/bins/env`
map onto the spec's `compatibility` string; `action.command/script` onto the
`scripts/` convention. Recommendation: (a) keep REMY's rich fields
(`triggers`/`watch`/`inject`/`handler`) under `metadata:`/`x-remy:` so a stock
loader still parses REMY skills, (b) enforce the spec's `name` regex + dir-match
(REMY doesn't), and (c) adopt progressive disclosure — the single biggest
context win.

## Lift
The frontmatter schema + validation rules + progressive-disclosure loading.

## Avoid
Depending on the bundled doc skills (docx/pdf/pptx/xlsx are source-available,
not OSS).

## License constraint
Apache-2.0 (spec) — portable with attribution.

## Effort
**S** (frontmatter alignment + validator) / **M** (progressive-disclosure loader).
