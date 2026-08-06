import json
import urllib.error
import urllib.request

import pytest

from remy.secrets.broker import TokenBroker
from remy.secrets.detect import (age_available, identity_file_secure,
                                 secrets_dir_secure)
from remy.secrets.scrub import scrub_env
from remy.secrets.store import AgeBackend, SecretStore


# --- store (injected fake backend, no age binary needed) --------------------

class _FakeBackend:
    """Reversible transform (marker + reversed bytes) so the stored form doesn't
    contain the plaintext — no real crypto needed to exercise the store."""
    def encrypt(self, plaintext: bytes) -> bytes:
        return b"ENC:" + plaintext[::-1]

    def decrypt(self, ciphertext: bytes) -> bytes:
        assert ciphertext.startswith(b"ENC:")
        return ciphertext[4:][::-1]


def store(tmp_path) -> SecretStore:
    return SecretStore(tmp_path / "secrets", _FakeBackend())


def test_put_get_roundtrip(tmp_path):
    s = store(tmp_path)
    s.put("github", "gho_secret_value")
    assert s.get("github") == "gho_secret_value"


def test_stored_file_is_encrypted_on_disk(tmp_path):
    s = store(tmp_path)
    s.put("github", "plaintext_secret")
    raw = (tmp_path / "secrets" / "github.age").read_bytes()
    assert b"plaintext_secret" not in raw
    assert raw.startswith(b"ENC:")


def test_names_and_delete(tmp_path):
    s = store(tmp_path)
    s.put("github", "a")
    s.put("google", "b")
    assert s.names() == ["github", "google"]
    assert s.delete("github") is True
    assert s.names() == ["google"]
    assert s.delete("github") is False


def test_get_missing_is_none(tmp_path):
    assert store(tmp_path).get("nope") is None


def test_bad_names_rejected(tmp_path):
    s = store(tmp_path)
    for bad in ("../escape", "a/b", ".hidden", ""):
        with pytest.raises(ValueError):
            s.put(bad, "x")


# --- age backend argv (verified without running age) ------------------------

def test_age_argv_shape():
    from pathlib import Path
    age = AgeBackend(recipient="age1xyz", identity_file="/k/id.txt")
    assert age.encrypt_argv() == ["age", "-r", "age1xyz", "-o", "-"]
    # identity path is stored as a Path; compare OS-normalized
    assert age.decrypt_argv() == ["age", "-d", "-i", str(Path("/k/id.txt"))]


# --- env scrub --------------------------------------------------------------

def test_scrub_drops_secrets_keeps_auth_and_path():
    env = {
        "PATH": "/usr/bin",
        "HOME": "/home/remy",
        "CLAUDE_CODE_OAUTH_TOKEN": "keep-me",
        "ANTHROPIC_API_KEY": "drop",
        "GH_TOKEN": "drop",
        "SPOTIFY_CLIENT_SECRET": "drop",
    }
    out = scrub_env(env)
    assert out["CLAUDE_CODE_OAUTH_TOKEN"] == "keep-me"
    assert out["PATH"] == "/usr/bin"
    for gone in ("ANTHROPIC_API_KEY", "GH_TOKEN", "SPOTIFY_CLIENT_SECRET"):
        assert gone not in out


def test_scrub_is_case_insensitive_and_drops_broker_bearer():
    env = {
        "spotify_client_secret": "drop",   # lowercase variant
        "Anthropic_Api_Key": "drop",        # mixed case
        "REMY_CRED_TOKEN": "drop",          # a leaked broker bearer
        "PATH": "/usr/bin",
    }
    out = scrub_env(env)
    assert list(out) == ["PATH"]


# --- broker auth logic (pure) -----------------------------------------------

class _Static:
    def __init__(self, name, token):
        self.name = name
        self._token = token

    def access_token(self):
        return (self._token, 9_999_999_999.0)


def test_handle_rejects_unknown_bearer():
    broker = TokenBroker()
    broker.register(_Static("github", "tok"))
    status, body = broker._handle("/token/github", "not-a-bearer")
    assert status == 403


def test_handle_rejects_provider_mismatch():
    broker = TokenBroker()
    broker.register(_Static("github", "tok"))
    broker.register(_Static("google", "tok2"))
    env = broker.grant("github")
    status, _ = broker._handle("/token/google", env["REMY_CRED_TOKEN"])
    assert status == 403  # bearer granted for github, not google


def test_grant_unknown_provider_raises():
    with pytest.raises(KeyError):
        TokenBroker().grant("nope")


def test_revoke_invalidates_bearer():
    broker = TokenBroker()
    broker.register(_Static("github", "tok"))
    env = broker.grant("github")
    bearer = env["REMY_CRED_TOKEN"]
    assert broker._handle("/token/github", bearer)[0] == 200
    broker.revoke(bearer)
    assert broker._handle("/token/github", bearer)[0] == 403


# --- broker over real loopback (works cross-platform) -----------------------

def test_broker_serves_token_over_http_but_not_the_refresh_secret():
    broker = TokenBroker()
    broker.register(_Static("github", "short-lived-access-token"))
    broker.start()
    try:
        env = broker.grant("github")
        req = urllib.request.Request(
            f"{env['REMY_CRED_URL']}/token/github",
            headers={"Authorization": f"Bearer {env['REMY_CRED_TOKEN']}"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            body = json.loads(resp.read().decode())
        assert body["access_token"] == "short-lived-access-token"
        assert "refresh" not in json.dumps(body).lower()

        # wrong bearer is refused
        bad = urllib.request.Request(f"{env['REMY_CRED_URL']}/token/github",
                                     headers={"Authorization": "Bearer wrong"})
        with pytest.raises(urllib.error.HTTPError) as exc:
            urllib.request.urlopen(bad, timeout=5)
        assert exc.value.code == 403
    finally:
        broker.stop()


# --- detection (never raises) -----------------------------------------------

def test_detect_helpers_return_bool(tmp_path):
    assert isinstance(age_available(), bool)
    assert secrets_dir_secure(tmp_path / "absent") is True  # missing dir is fine
    assert identity_file_secure(tmp_path / "absent.txt") is True  # absent is fine


def test_identity_file_insecure_when_world_readable(tmp_path):
    import os
    import sys
    if sys.platform == "win32":
        return  # POSIX mode bits don't apply on Windows
    ident = tmp_path / "identity.txt"
    ident.write_text("AGE-SECRET-KEY-...")
    os.chmod(ident, 0o644)
    assert identity_file_secure(ident) is False
    os.chmod(ident, 0o600)
    assert identity_file_secure(ident) is True
