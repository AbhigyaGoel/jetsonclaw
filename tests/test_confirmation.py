import pytest

from jetsonclaw.router.intents import is_affirmation, is_negation, parse


@pytest.mark.parametrize("text", ["yes", "Yeah do it", "sure", "go ahead",
                                  "hey jarvis yes", "proceed."])
def test_affirmations(text):
    assert is_affirmation(text)
    assert not is_negation(text)


@pytest.mark.parametrize("text", ["no", "nope", "cancel that", "never mind",
                                  "Jarvis, abort"])
def test_negations(text):
    assert is_negation(text)
    assert not is_affirmation(text)


@pytest.mark.parametrize("text", ["play some music", "what time is it",
                                  "yesterday was fun"])
def test_ordinary_text_is_neither(text):
    assert not is_affirmation(text)
    assert not is_negation(text)


@pytest.mark.parametrize("text", ["forget that", "new topic", "clean slate",
                                  "forget everything"])
def test_chat_reset(text):
    assert parse(text).name == "chat.reset"


def test_forget_inside_sentence_is_not_reset():
    assert parse("don't forget that I like jazz").name == "chat"


def test_remember_intent():
    intent = parse("Remy, remember that the wifi password is hunter2")
    assert intent.name == "memory.remember"
    assert intent.slots["fact"] == "the wifi password is hunter2"


def test_recall_intent():
    intent = parse("what do you remember about my dentist")
    assert intent.name == "memory.recall"
    assert intent.slots["query"] == "my dentist"


def test_status_intent():
    assert parse("status report").name == "system.status"
    assert parse("sitrep").name == "system.status"
