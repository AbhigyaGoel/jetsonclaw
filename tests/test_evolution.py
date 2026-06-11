from jetsonclaw.skills.selfiterate import append_evolution


def test_journal_creates_with_header(tmp_path):
    journal = tmp_path / "EVOLUTION.md"
    append_evolution(journal, "add a weather skill", "created weather skill", "workspace", ts=0)
    text = journal.read_text()
    assert text.startswith("# EVOLUTION.md")
    assert "add a weather skill" in text
    assert "(workspace)" in text


def test_journal_appends_in_order(tmp_path):
    journal = tmp_path / "EVOLUTION.md"
    append_evolution(journal, "first", "ok", "abc1234", ts=0)
    append_evolution(journal, "second", "ok", "def5678", ts=1000)
    text = journal.read_text()
    assert text.count("# EVOLUTION.md") == 1
    assert text.index("first") < text.index("second")


def test_long_outcome_truncated(tmp_path):
    journal = tmp_path / "EVOLUTION.md"
    append_evolution(journal, "x", "y" * 1000, "abc", ts=0)
    assert len(journal.read_text()) < 500
