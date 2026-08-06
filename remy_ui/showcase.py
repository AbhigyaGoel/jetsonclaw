"""Showcase: every shape, across unrelated domains, rendered AND spoken.

The point of this file is to prove the framework is domain-blind. Nothing
here knows what fitness or CI or music *is*, each item is just data in a
shape, and the same six widgets + verbalizers handle all of it.

    python -m remy_ui.showcase          # TUI render + the spoken line for each
    python -m remy_ui.showcase --html   # writes showcase.html
"""

from __future__ import annotations

import re
import sys

from . import (
    CLAWD,
    Entry,
    Gauge,
    RaceBar,
    Ranking,
    Series,
    Status,
    Value,
    to_html,
    to_speech,
    to_terminal,
)
from .ascii_art import banner
from .frame import frame
from .render import html as _html
from .render import terminal as _terminal

# One spec per shape, each from a different world.
GALLERY = [
    Value(title="GitHub stars", value=1240, delta=38, caption="since last week"),
    Value(title="CPU temp", value=61, unit="°C", delta=-3, caption="Jetson, nominal"),
    Series(
        title="Steps this week",
        points=(6200, 8100, 7400, 9300, 10200, 8800, 11400),
        caption="daily · Mon→Sun",
    ),
    RaceBar(
        title="Dorm pizza poll",
        unit=" votes",
        as_percent=False,
        entries=(Entry("Pepperoni", 12), Entry("Mushroom", 5), Entry("BBQ", 9)),
        note="41 in the group chat",
    ),
    Ranking(
        title="tracks today",
        top=3,
        items=(
            Entry("Blinding Lights", 42),
            Entry("One Dance", 31),
            Entry("bad guy", 27),
            Entry("Levitating", 19),
        ),
        caption="from Spotify",
    ),
    Status(title="CI build", state="passing", level="ok", detail="3m ago on main"),
    Status(title="Front door", state="unlocked", level="warn", detail="since 4:12pm"),
    Gauge(title="Download · ubuntu.iso", value=3.4, target=5.2, unit="GB"),
    Gauge(title="Steps toward goal", value=8200, target=10000, caption="1,800 to go"),
    # The skeleton state: a panel appears instantly with no data, then fills
    # as fetches land. This is the time-to-first-pixel story.
    RaceBar(
        title="Dorm pizza poll · live",
        entries=(Entry("Pepperoni"), Entry("Mushroom")),
        note="waiting for votes...",
    ),
]


def _strip(s: str) -> str:
    return re.sub(r"\x1b\[[0-9;]*m", "", s)


def _terminal_demo(plain: bool = False) -> str:
    theme = CLAWD
    blocks = [_terminal.encode(banner(theme, "one framework · every shape"), theme), ""]
    for spec in GALLERY:
        panel = to_terminal(spec, theme)
        blocks.append(_strip(panel) if plain else panel)
        says = to_speech(spec)
        line = f"  ↳ says: “{says}”"
        blocks.append(line if plain else f"\x1b[38;2;138;133;120m{line}\x1b[0m")
        blocks.append("")
    return "\n".join(blocks)


def _html_demo() -> str:
    theme = CLAWD
    parts = [_html.encode(frame("CLAWD", banner(theme, "one framework · every shape"), theme), theme)]
    for spec in GALLERY:
        says = to_speech(spec)
        parts.append(
            "<div>"
            f"{to_html(spec, theme)}"
            f"<div style=\"color:#8a8578;font:13px ui-monospace,monospace;"
            f"padding:6px 4px 0\">↳ says: “{says}”</div>"
            "</div>"
        )
    inner = "\n".join(parts)
    return (
        "<!doctype html><meta charset=utf-8><title>remy_ui showcase</title>"
        "<body style='background:#0f0e0d;margin:0;padding:24px;"
        "display:flex;flex-direction:column;gap:20px;align-items:flex-start'>"
        f"{inner}</body>"
    )


def main(argv: list[str] | None = None) -> None:
    argv = sys.argv[1:] if argv is None else argv
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if "--html" in argv:
        import pathlib

        out = pathlib.Path(__file__).with_name("showcase.html")
        out.write_text(_html_demo(), encoding="utf-8")
        print(f"wrote {out}")
    else:
        print(_terminal_demo(plain="--plain" in argv))


if __name__ == "__main__":
    main()
