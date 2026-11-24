"""
tests/test_m365_auth.py — verify the Microsoft 365 OAuth2 helpers.

Why this exists
---------------
Two failure modes in the Outlook SMTP AUTH path are silent until a real
recipient gets mail:

  1. **The XOAUTH2 blob separator.** The SASL initial response is
     `base64("user=" + mailbox + \x01 + "auth=Bearer " + token + \x01\x01)`.
     The separator must be the byte 0x01, not the two-character string `^A`.
     A wrong separator produces a bare `535` from the server with no
     explanation, and it is the single most common mistake when hand-rolling
     XOAUTH2.

  2. **Token refresh.** The cached access token lives ~1h. If the refresh
     path silently no-ops, the pipeline keeps sending for an hour and then
     stops — usually overnight, when nobody is watching.

So we assert the exact bytes of the blob, and assert that the refresh path
makes the right HTTP call and writes the new token back to the cache.

What is NOT tested here: the live token endpoint and the live SMTP server.
Both need real credentials. Those are covered by the manual verification in
SETUP_OUTLOOK_SMTP.md.

Run:
    python3 -m tests.test_m365_auth
"""

import base64
import json
import os
import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent))

from lib import m365_auth
from lib import smtp_client


# ──────────────────────────────────────────────────────────────────
# XOAUTH2 blob
# ──────────────────────────────────────────────────────────────────
def test_xoauth2_blob_is_byte_exact():
    """The blob must be exactly user=..\\x01auth=Bearer ..\\x01\\x01, base64'd."""
    user = "alex.morgan@avilx.com"
    token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9"
    blob = m365_auth.build_xoauth2_blob(user, token)

    expected_raw = (b"user=" + user.encode()
                    + b"\x01auth=Bearer " + token.encode()
                    + b"\x01\x01")
    assert blob == base64.b64encode(expected_raw), (
        f"blob mismatch\n  got:      {blob!r}\n  expected: {base64.b64encode(expected_raw)!r}")

    # Decoding it back must give the raw wire format.
    decoded = base64.b64decode(blob)
    assert decoded.count(b"\x01") == 3, f"expected 3 separators, got {decoded.count(chr(1).encode())}"
    assert decoded.startswith(b"user="), "blob must start with 'user='"
    assert decoded.endswith(b"\x01\x01"), "blob must end with two 0x01 bytes"
    assert b"auth=Bearer " in decoded, "blob must contain 'auth=Bearer '"
    # The separator must be the single byte 0x01 — NOT the literal "^A".
    assert b"^A" not in decoded, "separator must be 0x01, not the literal '^A'"
    print("  ✓ build_xoauth2_blob() produces the exact XOAUTH2 wire format")


def test_xoauth2_initial_response():
    """The AUTH command argument must be 'XOAUTH2 <blob>'."""
    arg = m365_auth.build_xoauth2_initial_response("a@b.com", "tok")
    assert arg.startswith("XOAUTH2 "), f"expected 'XOAUTH2 ' prefix, got {arg[:20]!r}"
    blob = arg[len("XOAUTH2 "):]
    assert base64.b64decode(blob).startswith(b"user=a@b.com")
    print("  ✓ build_xoauth2_initial_response() prefixes the AUTH argument")


# ──────────────────────────────────────────────────────────────────
# Token cache
# ──────────────────────────────────────────────────────────────────
def test_cached_token_is_used_without_network():
    """A fresh cached access token must be returned with no HTTP call."""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "m365_token.json"
        path.write_text(json.dumps({
            "access_token": "cached-token",
            "refresh_token": "refresh-token",
            "expires_at": time.time() + 3600,
        }))

        def _boom(*a, **k):
            raise AssertionError("no HTTP call should be made for a fresh cached token")

        with patch.object(m365_auth, "_post_form", _boom):
            ok, token = m365_auth.get_access_token(path=path)
        assert ok, f"expected success, got {token!r}"
        assert token == "cached-token", f"expected the cached token, got {token!r}"
    print("  ✓ get_access_token() serves a fresh cached token without a network call")


def test_expired_token_triggers_refresh_and_recaches():
    """An expired access token must be refreshed and the new one written back."""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "m365_token.json"
        path.write_text(json.dumps({
            "access_token": "stale-token",
            "refresh_token": "refresh-token",
            "expires_at": time.time() - 10,  # already expired
        }))

        captured = {}

        def _fake_post(url, data, timeout=30):
            captured["url"] = url
            captured["data"] = data
            return True, {
                "access_token": "fresh-token",
                "refresh_token": "new-refresh-token",
                "expires_in": 3600,
            }

        with patch.object(m365_auth, "_post_form", _fake_post), \
                patch.object(m365_auth, "client_id", lambda: "client-123"), \
                patch.object(m365_auth, "client_secret", lambda: "secret-456"):
            ok, token = m365_auth.get_access_token(path=path)

        assert ok, f"expected success, got {token!r}"
        assert token == "fresh-token", f"expected the refreshed token, got {token!r}"
        assert captured["data"]["grant_type"] == "refresh_token", \
            f"expected grant_type=refresh_token, got {captured['data'].get('grant_type')!r}"
        assert captured["data"]["refresh_token"] == "refresh-token"
        assert "SMTP.Send" in captured["data"]["scope"], \
            f"scope must request SMTP.Send, got {captured['data'].get('scope')!r}"
        assert captured["data"]["client_id"] == "client-123"

        # The new token must be persisted, and the file must be 0600.
        saved = json.loads(path.read_text())
        assert saved["access_token"] == "fresh-token", "refreshed token was not written back"
        assert saved["refresh_token"] == "new-refresh-token"
        assert saved["expires_at"] > time.time()
        mode = oct(path.stat().st_mode & 0o777)
        assert mode == "0o600", f"token file must be 0600, got {mode}"
    print("  ✓ get_access_token() refreshes an expired token and recaches it (mode 0600)")


def test_no_cache_returns_actionable_message():
    """With no cache and no refresh token we fail with a message, not a crash."""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "m365_token.json"
        ok, msg = m365_auth.get_access_token(path=path)
        assert not ok, "expected failure when there is no cached token"
        assert "m365_auth" in msg, f"the message should point at the bootstrap command, got {msg!r}"
    print("  ✓ get_access_token() fails open with an actionable message")


def test_failed_refresh_clears_dead_cache():
    """A revoked consent must not be retried forever — the cache is cleared."""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "m365_token.json"
        path.write_text(json.dumps({
            "access_token": "stale",
            "refresh_token": "revoked",
            "expires_at": time.time() - 10,
        }))

        def _fake_post(url, data, timeout=30):
            return False, {"error": "invalid_grant", "error_description": "consent revoked"}

        with patch.object(m365_auth, "_post_form", _fake_post), \
                patch.object(m365_auth, "client_id", lambda: "c"), \
                patch.object(m365_auth, "client_secret", lambda: "s"):
            ok, msg = m365_auth.get_access_token(path=path)

        assert not ok, "expected failure after a revoked refresh token"
        assert not path.exists(), "the dead token cache should have been cleared"
    print("  ✓ get_access_token() clears the cache after a failed refresh")


# ──────────────────────────────────────────────────────────────────
# SMTP config
# ──────────────────────────────────────────────────────────────────
def test_smtp_config_defaults_to_gmail():
    """With nothing set, the config must stay on the Gmail path."""
    with patch.dict(os.environ, {}, clear=True):
        cfg = smtp_client.smtp_config()
    assert cfg["auth_mode"] == "gmail", f"expected gmail, got {cfg['auth_mode']!r}"
    assert cfg["host"] == "smtp.gmail.com", f"unexpected host {cfg['host']!r}"
    assert cfg["port"] == 465, f"unexpected port {cfg['port']!r}"
    assert cfg["use_ssl"] is True, "gmail on 465 should use SSL"
    print("  ✓ smtp_config() defaults to the Gmail path (smtp.gmail.com:465, SSL)")


def test_smtp_config_oauth2_maps_to_outlook():
    """SMTP_AUTH=oauth2 must select Outlook SMTP AUTH on 587."""
    env = {
        "SMTP_AUTH": "oauth2",
        "AVILX_FROM_EMAIL": "alex.morgan@avilx.com",
    }
    with patch.dict(os.environ, env, clear=True):
        cfg = smtp_client.smtp_config()
    assert cfg["auth_mode"] == "oauth2", f"expected oauth2, got {cfg['auth_mode']!r}"
    assert cfg["host"] == "smtp-mail.outlook.com", f"unexpected host {cfg['host']!r}"
    assert cfg["port"] == 587, f"unexpected port {cfg['port']!r}"
    assert cfg["use_ssl"] is False, "Outlook SMTP AUTH uses STARTTLS on 587"
    assert cfg["user"] == "alex.morgan@avilx.com", f"unexpected user {cfg['user']!r}"
    assert cfg["password"] == "", "oauth2 must not carry a password"
    print("  ✓ smtp_config() maps SMTP_AUTH=oauth2 to smtp-mail.outlook.com:587 (STARTTLS)")


def test_smtp_config_prefers_avilx_namespace():
    """AVILX_SMTP_* must win over the legacy SMTP_* names."""
    env = {
        "AVILX_SMTP_HOST": "smtp-mail.outlook.com",
        "AVILX_SMTP_PORT": "587",
        "AVILX_SMTP_USER": "new@example.com",
        "AVILX_SMTP_PASS": "newpass",
        "SMTP_HOST": "smtp.gmail.com",
        "SMTP_PORT": "465",
        "SMTP_USERNAME": "old@example.com",
        "SMTP_PASSWORD": "oldpass",
    }
    with patch.dict(os.environ, env, clear=True):
        cfg = smtp_client.smtp_config()
    assert cfg["host"] == "smtp-mail.outlook.com", "AVILX_SMTP_HOST must win"
    assert cfg["port"] == 587, "AVILX_SMTP_PORT must win"
    assert cfg["user"] == "new@example.com", "AVILX_SMTP_USER must win"
    assert cfg["password"] == "newpass", "AVILX_SMTP_PASS must win"
    print("  ✓ smtp_config() prefers the AVILX_SMTP_* namespace over the legacy names")


def test_smtp_config_falls_back_to_legacy_names():
    """A legacy .env must keep working after the refactor."""
    env = {
        "SMTP_HOST": "smtp.gmail.com",
        "SMTP_PORT": "465",
        "SMTP_USERNAME": "legacy@example.com",
        "SMTP_PASSWORD": "legacypass",
    }
    with patch.dict(os.environ, env, clear=True):
        cfg = smtp_client.smtp_config()
    assert cfg["host"] == "smtp.gmail.com"
    assert cfg["port"] == 465
    assert cfg["user"] == "legacy@example.com"
    assert cfg["password"] == "legacypass"
    print("  ✓ smtp_config() still reads the legacy SMTP_* / GMAIL_* names")


# ──────────────────────────────────────────────────────────────────
# Retry classification
# ──────────────────────────────────────────────────────────────────
def test_permanent_vs_transient_classification():
    """Auth failures must never be retried; 4xx transient codes must be."""
    import smtplib

    assert smtp_client._is_permanent(smtplib.SMTPAuthenticationError(535, b"auth failed")), \
        "SMTPAuthenticationError must be permanent"
    assert smtp_client._is_permanent(smtplib.SMTPResponseException(535, b"nope")), \
        "535 (SMTP AUTH failed) must be permanent"
    assert smtp_client._is_permanent(
        smtplib.SMTPResponseException(550, b"5.7.1 Sender not authorized")), \
        "550 5.7.1 (sender not authorized) must be permanent"
    assert smtp_client._is_permanent(smtplib.SMTPRecipientsRefused({})), \
        "SMTPRecipientsRefused must be permanent"
    assert smtp_client._is_permanent(smtplib.SMTPSenderRefused(550, b"no", "alex@avilx.com")), \
        "SMTPSenderRefused must be permanent"

    assert not smtp_client._is_permanent(smtplib.SMTPResponseException(451, b"try later")), \
        "451 must be transient"
    assert not smtp_client._is_permanent(smtplib.SMTPServerDisconnected("boom")), \
        "SMTPServerDisconnected must be transient"
    assert not smtp_client._is_permanent(TimeoutError("slow")), \
        "a timeout must be transient"
    print("  ✓ _is_permanent() classifies auth failures as permanent and 4xx as transient")


if __name__ == "__main__":
    print("🧪 test_m365_auth")
    test_xoauth2_blob_is_byte_exact()
    test_xoauth2_initial_response()
    test_cached_token_is_used_without_network()
    test_expired_token_triggers_refresh_and_recaches()
    test_no_cache_returns_actionable_message()
    test_failed_refresh_clears_dead_cache()
    test_smtp_config_defaults_to_gmail()
    test_smtp_config_oauth2_maps_to_outlook()
    test_smtp_config_prefers_avilx_namespace()
    test_smtp_config_falls_back_to_legacy_names()
    test_permanent_vs_transient_classification()
    print("  ✅ all passed")
