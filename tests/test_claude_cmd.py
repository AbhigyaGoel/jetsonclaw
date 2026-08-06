from remy.brain.claude import ClaudeBridge, deny_settings
from remy.config import ClaudeConfig


def bridge(**kw) -> ClaudeBridge:
    return ClaudeBridge(ClaudeConfig(**kw))


def test_base_cmd_has_no_shell_tool():
    cmd = bridge().build_cmd("do a thing")
    tools = cmd[cmd.index("--allowedTools") + 1]
    assert "Bash" not in tools
    assert "--continue" not in cmd
    assert "--mcp-config" not in cmd


def test_deny_settings_denies_reading_secrets():
    deny = deny_settings(ClaudeConfig())["permissions"]["deny"]
    assert "Read(~/.remy/secrets/**)" in deny
    assert "Read(~/spotify_tokens.json)" in deny


def test_base_cmd_passes_deny_settings_file():
    b = bridge()
    cmd = b.build_cmd("do a thing")
    assert "--settings" in cmd
    assert cmd[cmd.index("--settings") + 1] == str(b.settings_path())


def test_no_settings_flag_when_deny_disabled():
    assert "--settings" not in bridge(deny_read=()).build_cmd("task")


def test_write_settings_persists_deny_list(tmp_path):
    target = tmp_path / "agent-settings.json"
    b = bridge(agent_settings_file=str(target))
    path = b.write_settings()
    assert path == target
    import json
    written = json.loads(target.read_text())
    assert "Read(~/.remy/secrets/**)" in written["permissions"]["deny"]


def test_continue_session_flag():
    assert "--continue" in bridge().build_cmd("keep going", continue_session=True)


def test_mcp_config_passthrough():
    cmd = bridge(mcp_config="~/mcp.json").build_cmd("task")
    assert "--mcp-config" in cmd
    assert cmd[cmd.index("--mcp-config") + 1].endswith("mcp.json")


def test_system_append_included():
    cmd = bridge().build_cmd("task", system_append="persona here")
    assert cmd[cmd.index("--append-system-prompt") + 1] == "persona here"
