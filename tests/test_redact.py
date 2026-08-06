from remy.redact import redact


def test_strips_github_token():
    out = redact("here is my token ghp_" + "A" * 36 + " ok")
    assert "ghp_" not in out
    assert "[redacted:github-token]" in out


def test_strips_google_oauth_and_api_key():
    assert "[redacted:google-oauth]" in redact("ya29." + "a.bc-D_e" * 5)
    assert "[redacted:google-api-key]" in redact("AIza" + "B" * 35)


def test_strips_openai_anthropic_and_slack_and_aws():
    assert "[redacted:openai-anthropic-key]" in redact("sk-ant-" + "x" * 40)
    assert "[redacted:slack-token]" in redact("xoxb-" + "1" * 20)
    assert "[redacted:aws-access-key]" in redact("AKIA" + "ABCDEFGHIJ123456")


def test_strips_bearer_but_keeps_scheme():
    out = redact("Authorization: Bearer " + "z" * 40)
    assert "Bearer [redacted:bearer]" in out
    assert "z" * 40 not in out


def test_strips_json_credential_values_keeps_keys():
    out = redact('{"refresh_token": "abcdef123456", "name": "chud"}')
    assert '"refresh_token": "[redacted]"' in out
    assert '"name": "chud"' in out  # ordinary fields untouched


def test_leaves_ordinary_speech_alone():
    speech = "play blinding lights and remind me to call mom at six"
    assert redact(speech) == speech


def test_empty_is_safe():
    assert redact("") == ""
