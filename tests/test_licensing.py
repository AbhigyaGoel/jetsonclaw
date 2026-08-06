from remy.licensing import _is_gpl_piper, gpl_piper_installed


def test_gpl_by_license_text():
    assert _is_gpl_piper("1.4.2", "GPLv3") is True
    assert _is_gpl_piper("0.0.0", "GNU General Public License") is True


def test_gpl_by_version_line():
    assert _is_gpl_piper("1.3.0", "") is True   # piper1-gpl line
    assert _is_gpl_piper("1.5.1", "UNKNOWN") is True


def test_mit_era_is_clean():
    assert _is_gpl_piper("1.2.0", "MIT") is False
    assert _is_gpl_piper("1.1.0", "") is False


def test_bad_version_string_is_not_gpl():
    assert _is_gpl_piper("weird", "MIT") is False


def test_guard_blocks_selftest_when_gpl_piper_present():
    # The selftest gate must stay red while a GPL Piper is importable in-process.
    # In a clean env piper-tts is absent, so this is None; if it ever fails,
    # `pip uninstall piper-tts` and use the binary.
    assert gpl_piper_installed() is None
