import urllib.parse

from remy.skills.spotify_auth import SCOPES, authorize_url, redirect_uri


def test_redirect_uri_uses_loopback_not_localhost():
    uri = redirect_uri(8888)
    assert uri == "http://127.0.0.1:8888/callback"
    assert "localhost" not in uri  # Spotify rejects localhost since 2025


def test_redirect_uri_honors_port():
    assert redirect_uri(9001).startswith("http://127.0.0.1:9001/")


def test_authorize_url_is_a_code_flow_with_loopback_redirect():
    url = authorize_url("my_client_id", port=8888)
    parsed = urllib.parse.urlparse(url)
    query = urllib.parse.parse_qs(parsed.query)
    assert parsed.netloc == "accounts.spotify.com"
    assert query["response_type"] == ["code"]
    assert query["client_id"] == ["my_client_id"]
    assert query["redirect_uri"] == ["http://127.0.0.1:8888/callback"]


def test_authorize_url_requests_playback_scopes():
    query = urllib.parse.parse_qs(urllib.parse.urlparse(authorize_url("cid")).query)
    scope = query["scope"][0]
    assert "user-modify-playback-state" in scope
    assert set(SCOPES).issubset(set(scope.split()))
