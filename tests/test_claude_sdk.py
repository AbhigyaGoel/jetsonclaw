from remy.brain.claude import ClaudeBridge, make_bridge
from remy.brain.claude_sdk import ClaudeSDKBridge
from remy.config import ClaudeConfig


def sdk_bridge(**kw) -> ClaudeSDKBridge:
    return ClaudeSDKBridge(ClaudeConfig(engine="sdk", **kw))


# --- engine selection -------------------------------------------------------

def test_make_bridge_defaults_to_cli():
    assert isinstance(make_bridge(ClaudeConfig()), ClaudeBridge)


def test_make_bridge_sdk_when_selected():
    assert isinstance(make_bridge(ClaudeConfig(engine="sdk")), ClaudeSDKBridge)


def test_sdk_unavailable_without_package():
    # The SDK isn't a hard dep; off-box it's absent, so the bridge reports so
    # instead of crashing (the CLI stays the default engine).
    import importlib.util
    installed = importlib.util.find_spec("claude_agent_sdk") is not None
    assert sdk_bridge().available() is installed


# --- option mapping (pure, no SDK needed) -----------------------------------

def test_option_kwargs_defaults():
    kw = sdk_bridge()._option_kwargs(None, None, False, None)
    assert kw["cwd"].endswith("remy")
    assert isinstance(kw["allowed_tools"], list)
    assert "Bash" not in kw["allowed_tools"]
    assert kw["permission_mode"] == "acceptEdits"
    assert kw["settings"].endswith("agent-settings.json")
    for absent in ("resume", "continue_conversation", "system_prompt", "mcp_servers"):
        assert absent not in kw


def test_option_kwargs_appends_system_prompt():
    kw = sdk_bridge()._option_kwargs(None, "persona here", False, None)
    assert kw["system_prompt"] == {
        "type": "preset", "preset": "claude_code", "append": "persona here"}


def test_option_kwargs_resume_beats_continue():
    kw = sdk_bridge()._option_kwargs(None, None, True, "sid-123")
    assert kw["resume"] == "sid-123"
    assert "continue_conversation" not in kw


def test_option_kwargs_continue_when_no_resume():
    kw = sdk_bridge()._option_kwargs(None, None, True, None)
    assert kw["continue_conversation"] is True
    assert "resume" not in kw


def test_option_kwargs_omits_settings_when_deny_disabled():
    assert "settings" not in sdk_bridge(deny_read=())._option_kwargs(None, None, False, None)


# --- message mapping with injected stand-ins --------------------------------

class _Text:
    def __init__(self, text): self.text = text


class _Tool:
    def __init__(self, name): self.name = name


class _Assistant:
    def __init__(self, content): self.content = content


class _Result:
    def __init__(self, result="", is_error=False, session_id="",
                 total_cost_usd=None, usage=None):
        self.result, self.is_error, self.session_id = result, is_error, session_id
        self.total_cost_usd, self.usage = total_cost_usd, usage


def _map(msg):
    return ClaudeSDKBridge._map(msg, _Assistant, _Text, _Tool, _Result)


def test_map_text_block():
    lines = _map(_Assistant([_Text("  hi there ")]))
    assert [(ln.kind, ln.text) for ln in lines] == [("text", "hi there")]


def test_map_tool_then_text():
    lines = _map(_Assistant([_Tool("Read"), _Text("ok")]))
    assert [ln.kind for ln in lines] == ["tool", "text"]
    assert lines[0].text == "Read"


def test_map_result_carries_session_then_result():
    lines = _map(_Result(result="done", session_id="abc"))
    assert [(ln.kind, ln.text) for ln in lines] == [("session", "abc"), ("result", "done")]


def test_map_result_error():
    lines = _map(_Result(result="boom", is_error=True))
    assert lines[-1].kind == "error"
    assert "boom" in lines[-1].text


def test_map_result_carries_cost():
    lines = _map(_Result(result="done", session_id="abc", total_cost_usd=0.5,
                         usage={"input_tokens": 10, "output_tokens": 3}))
    result = lines[-1]
    assert result.kind == "result"
    assert result.cost_usd == 0.5
    assert result.usage["input_tokens"] == 10


def test_smoke_sdk_imports_when_present():
    import pytest
    pytest.importorskip("claude_agent_sdk")
    from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient  # noqa: F401
    assert sdk_bridge().available() is True
