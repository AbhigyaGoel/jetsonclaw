# remy_ui

REMY's display layer. One tiny spec, and the same widget shows up in the
terminal TUI and the phone web app, drawn in the Claude Code / CLAWD terminal
look. No per-request codegen, so it lands on screen the instant you ask.

```
╭─ ✻ favorite Kanye ──────────────────────╮
│ 1. Runaway          ██████████████  512 │
│ 2. Stronger         ████████████░░  441 │
│ 3. Power            ███████████░░░  388 │
│ ranked by your plays                    │
╰─────────────────────────────────────────╯
```

## The trick

An LLM can't generate and deploy a UI in 300ms. So it doesn't. All the work
happens here, at build time. At request time REMY emits about 200 bytes of
spec and a prebuilt renderer paints it.

```
spec  ->  rows (styled segments)  ->  ANSI   (TUI)
                                  ->  <pre>   (web app)
```

Widgets never touch ANSI or HTML. They emit styled `Segment` rows, and a
renderer encodes those for whichever surface. You can add a new surface
without opening a single widget, and change the entire look by editing
`theme.py`.

## Shapes, not topics

Widgets are typed by the shape of the data, never the subject. There's no
"election widget" or "weather widget," because those are just data. Six shapes
cover almost anything you'd ask a voice assistant to show:

| Shape | Shows | Fits |
|-------|-------|------|
| `Value` | one number and its change | followers, temp, price |
| `RaceBar` | things measured against each other | polls, load by host |
| `Series` | a value over time, as a sparkline | forecasts, latency |
| `Ranking` | an ordered leaderboard | top tracks, top processes |
| `Status` | a state with a level | build passing, door locked |
| `Gauge` | progress toward a target | downloads, goals, disk |

Every shape does two things: it draws, and it speaks. `to_speech(spec)` turns
the same spec into a sentence for Piper, because a voice assistant needs both.

## Use it

```python
from remy_ui import Ranking, Entry, to_terminal, to_html, to_speech

spec = Ranking(
    title="favorite Kanye",
    items=(Entry("Runaway", 512), Entry("Stronger", 441), Entry("Power", 388)),
    caption="ranked by your plays",
)

to_terminal(spec)   # ANSI for the TUI
to_html(spec)       # <pre> fragment for the web app
to_speech(spec)     # "Top favorite Kanye: Runaway, then Stronger."
```

Panels show up before the data does. Build a spec with `value=None` and you
get a dim skeleton with placeholders, so the frame is on screen the moment you
ask. Refill it as each fetch lands.

## See it

```
python -m remy_ui.showcase          # every shape, nine domains, drawn and spoken
python -m remy_ui.showcase --html   # the same thing as a web page
python remy_ui/tests/test_race_bar.py
python remy_ui/tests/test_shapes.py
```

## Layout

```
theme.py      palette, glyphs, semantic colors. the whole look.
segment.py    Segment and Row, the surface-agnostic middle.
spec.py       the shape specs. frozen, self-validating.
frame.py      the rounded panel, itself just styled rows.
widgets/      one file per shape. build() returns rows.
render/       terminal.py (ANSI), html.py (<pre>), dispatch.
verbalize.py  the speak half. a shape to a sentence.
numfmt.py     number formatting, shared by screen and voice.
ascii_art.py  the CLAWD banner.
showcase.py   the demo.
tests/        17 tests.
```

The data that fills these lives one layer up, in `remy_core`.
