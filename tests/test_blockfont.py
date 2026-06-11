from remy.tui.blockfont import render_block


def test_six_lines():
    assert len(render_block("HI").splitlines()) == 6


def test_unknown_chars_render_as_space():
    out = render_block("A#B")
    assert len(out.splitlines()) == 6


def test_lowercase_uppercased():
    assert render_block("hi") == render_block("HI")
