from pathlib import Path

from jetsonclaw.brain.episodic import EpisodicStore, _keywords

DAY = 86400.0
NOW = DAY * 20000  # fixed fake "now", far from epoch


def store_with(tmp_path: Path, items) -> EpisodicStore:
    store = EpisodicStore(tmp_path / "memory")
    for ts, user, reply in items:
        store.append(user, reply, "chat", ts=ts)
    return store


def test_append_and_read_roundtrip(tmp_path):
    store = store_with(tmp_path, [(NOW, "hello", "hi there")])
    episodes = store.all()
    assert len(episodes) == 1
    assert episodes[0].user == "hello"


def test_search_finds_keyword_match(tmp_path):
    store = store_with(tmp_path, [
        (NOW - 2 * DAY, "remind me to buy guitar strings", "Noted."),
        (NOW - 2 * DAY, "play some jazz", "Playing jazz."),
    ])
    hits = store.search("what did I say about the guitar", now=NOW)
    assert len(hits) == 1
    assert "guitar" in hits[0].user


def test_search_skips_recent_episodes(tmp_path):
    store = store_with(tmp_path, [(NOW - 60, "guitar strings", "Noted.")])
    assert store.search("guitar", now=NOW) == []


def test_search_prefers_recent_over_old(tmp_path):
    store = store_with(tmp_path, [
        (NOW - 300 * DAY, "the wifi password is hunter2", "Got it."),
        (NOW - 1 * DAY, "the wifi password changed to hunter3", "Updated."),
    ])
    hits = store.search("what's the wifi password", now=NOW, limit=2)
    assert "hunter3" in hits[0].user


def test_on_day_and_unconsolidated(tmp_path):
    store = store_with(tmp_path, [
        (NOW - 2 * DAY, "old question", "old answer"),
        (NOW, "today question", "today answer"),
    ])
    old_day = store.all()[0].day
    assert len(store.on_day(old_day)) == 1
    assert store.unconsolidated_days(now=NOW) == [old_day]
    (store.dir / f"{old_day}.md").write_text("# done")
    assert store.unconsolidated_days(now=NOW) == []


def test_keywords_drop_stopwords():
    assert "guitar" in _keywords("what about the guitar")
    assert "the" not in _keywords("what about the guitar")


def test_recent_turns_and_prompt(tmp_path):
    store = store_with(tmp_path, [
        (NOW - 60, "what's the weather", "Sunny, sir."),
        (NOW - 30, "thanks", "Anytime."),
    ])
    prompt = store.as_prompt("what about tomorrow", now=NOW)
    assert "Sunny, sir." in prompt
    assert prompt.rstrip().endswith("Assistant:")


def test_context_floor_clears_working_memory(tmp_path):
    store = store_with(tmp_path, [(NOW - 60, "secret stuff", "Noted.")])
    assert store.as_prompt("hi", now=NOW, floor=NOW - 10) == "hi"


def test_working_memory_capped_at_max_turns(tmp_path):
    store = store_with(tmp_path,
                       [(NOW - 500 + i, f"q{i}", f"a{i}") for i in range(10)])
    turns = store.recent_turns(now=NOW)
    assert len(turns) == store.WORKING_MAX_TURNS
    assert turns[-1].user == "q9"


def test_search_summaries(tmp_path):
    store = EpisodicStore(tmp_path / "memory")
    store.dir.mkdir(parents=True)
    (store.dir / "2026-06-09.md").write_text(
        "# 2026-06-09\n\n## Summary\n- discussed the dentist appointment\n- played jazz\n")
    (store.dir / "2026-06-10.md").write_text(
        "# 2026-06-10\n\n## Summary\n- talked about guitar strings\n")
    hits = store.search_summaries("dentist")
    assert len(hits) == 1
    assert hits[0].startswith("[2026-06-09]")
    assert store.search_summaries("zebra") == []
