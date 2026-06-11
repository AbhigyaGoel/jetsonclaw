from remy.brain.chat import ChatBrain
from remy.config import ChatConfig


def brain(**kw) -> ChatBrain:
    return ChatBrain(ChatConfig(**kw))


def test_ollama_payload_shape():
    p = brain().payload("hi", "extra context", stream=True)
    assert p["prompt"] == "hi"
    assert "extra context" in p["system"]
    assert p["stream"] is True
    assert p["keep_alive"] == "24h"


def test_openai_payload_shape():
    p = brain(provider="openai", model="llama-3.3-70b").payload("hi", "", stream=False)
    assert p["model"] == "llama-3.3-70b"
    assert p["messages"][0]["role"] == "system"
    assert p["messages"][1] == {"role": "user", "content": "hi"}
    assert "keep_alive" not in p
    assert p["max_tokens"] == 150


def test_openai_stream_line_parsing():
    b = brain(provider="openai")
    assert b._parse_stream_line(b'data: {"choices":[{"delta":{"content":"Hel"}}]}') == "Hel"
    assert b._parse_stream_line(b"data: [DONE]") is None
    assert b._parse_stream_line(b": keepalive comment") == ""


def test_ollama_stream_line_parsing():
    b = brain()
    assert b._parse_stream_line(b'{"response":"Hel","done":false}') == "Hel"
    assert b._parse_stream_line(b'{"response":"","done":true}') is None
    assert b._parse_stream_line(b"not json") == ""


def test_api_key_header_only_when_env_set(monkeypatch):
    b = brain(provider="openai", api_key_env="TEST_CHAT_KEY")
    monkeypatch.delenv("TEST_CHAT_KEY", raising=False)
    assert "Authorization" not in b._headers()
    monkeypatch.setenv("TEST_CHAT_KEY", "sk-test")
    assert b._headers()["Authorization"] == "Bearer sk-test"


def test_legacy_ollama_section_still_loads(tmp_path, monkeypatch):
    monkeypatch.setattr("remy.config.DEFAULT_CONFIG_PATHS", ())
    path = tmp_path / "config.toml"
    path.write_text('[ollama]\nmodel = "qwen2.5:7b"\n')
    from remy.config import load_config

    assert load_config(path).chat.model == "qwen2.5:7b"
