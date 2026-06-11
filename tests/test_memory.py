from jetsonclaw.brain.memory import ConversationMemory


def test_empty_memory_passes_text_through():
    mem = ConversationMemory()
    assert mem.as_prompt("hello") == "hello"


def test_history_rendered_in_prompt():
    mem = ConversationMemory()
    mem.add("what's the weather", "Sunny, sir.", now=100.0)
    prompt = mem.as_prompt("what about tomorrow", now=101.0)
    assert "what's the weather" in prompt
    assert "Sunny, sir." in prompt
    assert prompt.rstrip().endswith("JARVIS:")


def test_ttl_expires_old_turns():
    mem = ConversationMemory(ttl_secs=60)
    mem.add("old question", "old answer", now=0.0)
    assert mem.as_prompt("new question", now=1000.0) == "new question"


def test_max_turns_keeps_most_recent():
    mem = ConversationMemory(max_turns=2)
    for i in range(5):
        mem.add(f"q{i}", f"a{i}", now=float(i))
    prompt = mem.as_prompt("next", now=5.0)
    assert "q0" not in prompt and "q4" in prompt


def test_clear():
    mem = ConversationMemory()
    mem.add("q", "a", now=100.0)
    mem.clear()
    assert mem.as_prompt("x", now=101.0) == "x"


def test_add_does_not_mutate_shared_list():
    mem = ConversationMemory()
    before = mem.recent(now=0.0)
    mem.add("q", "a", now=100.0)
    assert before == []  # snapshot unchanged — list was replaced, not mutated
