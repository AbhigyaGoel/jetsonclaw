from jetsonclaw.brain.ollama import split_complete_sentences


def test_no_boundary_keeps_buffering():
    sentences, rest = split_complete_sentences("Hello there")
    assert sentences == []
    assert rest == "Hello there"


def test_single_complete_sentence():
    sentences, rest = split_complete_sentences("Hello there. How are")
    assert sentences == ["Hello there."]
    assert rest == "How are"


def test_multiple_sentences():
    sentences, rest = split_complete_sentences("One. Two! Three? Four")
    assert sentences == ["One.", "Two!", "Three?"]
    assert rest == "Four"


def test_trailing_period_without_space_is_not_split():
    # "3.14" style — no whitespace after the period, must keep buffering
    sentences, rest = split_complete_sentences("Pi is 3.14159")
    assert sentences == []
    assert rest == "Pi is 3.14159"
