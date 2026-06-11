from remy.brain.claude import ClaudeBridge
from remy.config import ClaudeConfig


def bridge(**kw) -> ClaudeBridge:
    return ClaudeBridge(ClaudeConfig(**kw))


def test_base_cmd_has_no_shell_tool():
    cmd = bridge().build_cmd("do a thing")
    tools = cmd[cmd.index("--allowedTools") + 1]
    assert "Bash" not in tools
    assert "--continue" not in cmd
    assert "--mcp-config" not in cmd


def test_continue_session_flag():
    assert "--continue" in bridge().build_cmd("keep going", continue_session=True)


def test_mcp_config_passthrough():
    cmd = bridge(mcp_config="~/mcp.json").build_cmd("task")
    assert "--mcp-config" in cmd
    assert cmd[cmd.index("--mcp-config") + 1].endswith("mcp.json")


def test_system_append_included():
    cmd = bridge().build_cmd("task", system_append="persona here")
    assert cmd[cmd.index("--append-system-prompt") + 1] == "persona here"
