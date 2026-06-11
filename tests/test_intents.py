"""Intent parsing tests — this is the contract the voice router lives by."""

import pytest

from jetsonclaw.router.intents import parse


@pytest.mark.parametrize("text,expected", [
    ("skip this", "spotify.next"),
    ("next song please", "spotify.next"),
    ("pause", "spotify.pause"),
    ("stop the music", "spotify.pause"),
    ("resume", "spotify.resume"),
    ("play", "spotify.resume"),
    ("play music", "spotify.resume"),
    ("what's playing?", "spotify.now_playing"),
    ("what song is this", "spotify.now_playing"),
])
def test_spotify_basic(text, expected):
    assert parse(text).name == expected


def test_play_track_extracts_query():
    intent = parse("play blinding lights")
    assert intent.name == "spotify.play_track"
    assert intent.slots["query"] == "blinding lights"


def test_play_track_strips_wake_prefix_and_punctuation():
    intent = parse("Hey Jarvis, play Starboy.")
    assert intent.name == "spotify.play_track"
    assert intent.slots["query"] == "starboy"


@pytest.mark.parametrize("text,name", [
    ("play my playlist gym mix", "gym mix"),
    ("play playlist late night drives", "late night drives"),
    ("play gym mix from my playlist", "gym mix"),
])
def test_play_playlist(text, name):
    intent = parse(text)
    assert intent.name == "spotify.play_playlist"
    assert intent.slots["name"] == name


@pytest.mark.parametrize("text", [
    "upgrade yourself to support timers",
    "improve your code so responses are faster",
    "Jarvis, fix your ui",
    "give yourself a weather skill",
])
def test_self_iterate(text):
    intent = parse(text)
    assert intent.name == "self.iterate"
    assert intent.slots["instruction"]


@pytest.mark.parametrize("text", [
    "undo that",
    "revert that change",
    "roll back the last update",
])
def test_rollback(text):
    assert parse(text).name == "self.rollback"


@pytest.mark.parametrize("text", [
    "what's my name?",
    "who am I",
    "do you know my name",
])
def test_identity(text):
    assert parse(text).name == "identity.name"


@pytest.mark.parametrize("text", [
    "edit the portfolio site to add my new project",
    "update my website with the new resume",
    "fix the bug in my blog deploy",
])
def test_agent_tasks(text):
    intent = parse(text)
    assert intent.name == "agent.task"
    assert intent.slots["instruction"]


@pytest.mark.parametrize("text", [
    "how far away is the moon",
    "tell me a joke",
    "what do you think about mondays",
])
def test_chat_fallback(text):
    intent = parse(text)
    assert intent.name == "chat"
    assert intent.slots["text"]


def test_chat_does_not_swallow_spotify():
    assert parse("hey jarvis what's playing right now").name == "spotify.now_playing"


def test_remy_wake_prefix_stripped():
    intent = parse("Hey Remy, play Starboy.")
    assert intent.name == "spotify.play_track"
    assert intent.slots["query"] == "starboy"


def test_your_name_is_self_not_owner():
    assert parse("what's your name?").name == "identity.self"
    assert parse("who are you").name == "identity.self"
    assert parse("what's my name?").name == "identity.name"


def test_agent_continue():
    intent = parse("keep going with the website changes")
    assert intent.name == "agent.continue"
    assert parse("continue").name == "agent.continue"


def test_volume_intents():
    assert parse("set the volume to 40").slots["percent"] == "40"
    assert parse("volume 75").name == "spotify.volume_set"
    assert parse("turn it up").name == "spotify.volume_delta"
    assert parse("quieter please").slots["delta"] == "-15"


def test_brief_start():
    assert parse("take a brief").name == "brief.start"
    assert parse("let me explain something").name == "brief.start"
    assert parse("i have a project for you").name == "brief.start"
