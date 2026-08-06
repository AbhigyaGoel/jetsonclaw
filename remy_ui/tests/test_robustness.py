"""Robustness: untrusted/international text and bad numbers must never break
alignment, leak escapes, or crash the renderer.

    python remy_ui/tests/test_robustness.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from remy_ui import (  # noqa: E402
    Entry,
    Gauge,
    RaceBar,
    Ranking,
    Status,
    Value,
    to_speech,
    to_terminal,
)
from remy_ui.text import cell_width, clean, truncate  # noqa: E402


def _content_cell_widths(spec) -> list[int]:
    """Cell width of every rendered line (borders included)."""
    plain = re.sub(r"\x1b\[[0-9;]*m", "", to_terminal(spec))
    return [cell_width(line) for line in plain.splitlines()]


# --- text hygiene ------------------------------------------------------------

def test_clean_strips_control_chars() -> None:
    # The ESC and BEL control bytes are removed; the printable remnant "[31m"
    # is harmless literal text once the escape that armed it is gone.
    cleaned = clean("a\x1b[31mb\x07c")
    assert "\x1b" not in cleaned and "\x07" not in cleaned
    assert cleaned == "a[31mbc"


def test_clean_nfc_normalizes_combining_accents() -> None:
    decomposed = "café"          # 'e' + combining acute accent
    precomposed = "café"          # single 'é'
    assert clean(decomposed) == precomposed
    assert cell_width(clean(decomposed)) == 4


def test_newline_becomes_space_not_a_new_row() -> None:
    assert Entry("line1\nline2", 5).label == "line1 line2"


# --- alignment under wide / weird characters --------------------------------

def test_cjk_labels_keep_box_aligned() -> None:
    # A Japanese title alongside an ASCII one: every rendered line must be the
    # same terminal-cell width or the right border drifts.
    spec = Ranking(title="top", items=(Entry("東京は夜", 5), Entry("Runaway", 3)))
    widths = _content_cell_widths(spec)
    assert len(set(widths)) == 1, f"box misaligned: {widths}"


def test_injected_escape_never_reaches_terminal() -> None:
    out = to_terminal(RaceBar(title="poll", entries=(Entry("\x1b[2JHACK", 5), Entry("b", 3))))
    assert "\x1b[2J" not in out                 # the armed clear-screen sequence is gone
    # No ESC byte survives in any sanitized field, so nothing can be armed.
    label = RaceBar(title="p", entries=(Entry("\x1b[2Jx", 1), Entry("y", 1))).entries[0].label
    assert "\x1b" not in label


# --- numeric edge cases ------------------------------------------------------

def test_nan_and_inf_render_without_crashing() -> None:
    for v in (float("nan"), float("inf"), float("-inf")):
        assert "n/a" in to_terminal(Value(title="x", value=v))          # must not raise
    to_terminal(Gauge(title="g", value=float("nan"), target=100))       # must not raise
    to_terminal(RaceBar(title="p", entries=(Entry("a", float("nan")), Entry("b", 3))))


# --- overflow ----------------------------------------------------------------

def test_long_title_is_capped() -> None:
    widths = _content_cell_widths(RaceBar(title="X" * 200, entries=(Entry("a", 1), Entry("b", 1))))
    assert max(widths) <= 60, f"title not capped: {max(widths)}"


def test_truncate_is_cell_aware() -> None:
    assert truncate("hello world", 6) == "hello…"
    assert cell_width(truncate("東京は夜の七時", 8)) <= 8
    assert truncate("hi", 0) == ""              # non-positive budget


# --- optional fields ---------------------------------------------------------

def test_whitespace_only_optionals_become_none() -> None:
    assert RaceBar(title="p", note="   ", entries=(Entry("a", 1), Entry("b", 1))).note is None
    assert Ranking(title="t", caption="  ", items=(Entry("a", 1),)).caption is None


# --- verbalizer correctness --------------------------------------------------

def test_value_zero_delta_is_spoken() -> None:
    assert "flat 0" in to_speech(Value(title="Errors", value=10, delta=0.0))


def test_status_with_detail_is_well_formed() -> None:
    said = to_speech(Status(title="CI build", state="passing", level="ok", detail="3m ago on main"))
    assert said.endswith(".")
    assert "3m ago on main" in said


def test_zero_value_entry_not_misranked() -> None:
    said = to_speech(RaceBar(
        title="poll", as_percent=False,
        entries=(Entry("Austin", 0), Entry("Miami", 5)),
    ))
    assert said.startswith("Miami leads Austin")


def _run_all() -> int:
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failed = 0
    for t in tests:
        try:
            t()
            print(f"  ok  {t.__name__}")
        except Exception as exc:  # noqa: BLE001
            failed += 1
            print(f"FAIL  {t.__name__}: {exc}")
    print(f"\n{len(tests) - failed}/{len(tests)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(_run_all())
