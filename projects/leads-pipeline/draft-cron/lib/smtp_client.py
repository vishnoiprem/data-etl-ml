"""
lib/smtp_client.py — the one place that opens an authenticated SMTP session.

Why this exists
---------------
The pipeline had **two** SMTP code paths that had drifted apart:

    autopilot.py            →  SMTP_HOST / SMTP_PORT / SMTP_USERNAME / SMTP_PASSWORD
    bin/send_followups.py   →  AVILX_SMTP_HOST / AVILX_SMTP_PORT / AVILX_SMTP_USER / ...

They used different env namespaces, different defaults, and only `autopilot.py`
had a retry wrapper. Every change to the sender identity had to be made twice,
and the second one was easy to forget. This module collapses both into one
client so there is exactly one place that knows how to authenticate.

Auth modes
----------
`SMTP_AUTH` selects the mechanism:

    gmail   (default) — password login. Host smtp.gmail.com:465 (SSL) or
                         :587 (STARTTLS). Identical to the historical
                         behaviour, so existing .env files keep working.
    oauth2             — Outlook SMTP AUTH. Host smtp-mail.outlook.com:587
                         (STARTTLS), then `AUTH XOAUTH2 <base64 blob>` using a
                         Microsoft Graph token from `lib.m365_auth.py`.

Why OAuth2 matters: Gmail accepts `MAIL FROM:<alex.morgan@avilx.com>` but
rewrites the delivered `From:` header to the Gmail login address, so mail
cannot genuinely arrive from `alex.morgan@avilx.com` over Gmail. Outlook SMTP
AUTH over a licensed Microsoft 365 mailbox does send from that address.

Env namespace
-------------
`AVILX_SMTP_*` wins. The legacy `SMTP_*` / `GMAIL_ADDRESS` /
`GMAIL_APP_PASSWORD` names are still read as a fallback so no existing
deployment breaks on upgrade.

Retry policy
------------
Moved here from `autopilot.py` so the follow-up path gets it too.

Permanent (raised immediately, never retried):
    - `SMTPAuthenticationError`   — bad password / rejected token
    - `SMTPResponseException` 535 — SMTP AUTH failed
    - `SMTPResponseException` 550 with "5.7.1" — sender not authorized
      (the mailbox isn't licensed, or lacks Send As for the From address)
    - `SMTPRecipientsRefused`     — hard bounce
    - `SMTPSenderRefused`         — From address rejected

Transient (retried with backoff 0s / 30s / 120s):
    - `SMTPResponseException` with 421/450/451/452/454
    - `SMTPServerDisconnected`, `SMTPConnectError`, `SMTPHeloError`,
      `SMTPDataError`, `socket.timeout`, `ConnectionError`, `OSError`

The OAuth failure modes must be classified *before* the broad
`smtplib.SMTPException` clause, otherwise a misconfigured token is retried
three times with two-minute sleeps for no reason.
"""

from __future__ import annotations

import os
import smtplib
import socket
import ssl
import sys
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Iterator, Optional

HERE = Path(__file__).resolve().parent
PROJECT_ROOT = HERE.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from lib import m365_auth  # noqa: E402 — needs the sys.path insert above

# Backoff in seconds before attempts 2 and 3.
RETRY_BACKOFF = (0, 30, 120)

# SMTP response codes that mean "try again later".
TRANSIENT_CODES = (421, 450, 451, 452, 454)


def _env(name: str, default: str = "") -> str:
    return (os.getenv(name, default) or "").strip()


# ──────────────────────────────────────────────────────────────────
# Config
# ──────────────────────────────────────────────────────────────────
def smtp_config() -> Dict[str, Any]:
    """Resolve the SMTP settings from the environment.

    Returns a dict with: auth_mode, host, port, user, password, use_ssl.
    """
    auth = (_env("SMTP_AUTH", "gmail").lower() or "gmail")
    if auth not in ("gmail", "oauth2"):
        auth = "gmail"

    if auth == "oauth2":
        host = _env("AVILX_SMTP_HOST", "smtp-mail.outlook.com")
        port = int(_env("AVILX_SMTP_PORT", "587") or 587)
        user = m365_auth.sender()
        password = ""
        use_ssl = _env("AVILX_SMTP_USE_SSL", "false").lower() == "true"
    else:
        host = (_env("AVILX_SMTP_HOST")
                or _env("SMTP_HOST", "smtp.gmail.com"))
        port = int(_env("AVILX_SMTP_PORT") or _env("SMTP_PORT", "465") or 465)
        user = (_env("AVILX_SMTP_USER")
                or _env("SMTP_USERNAME")
                or _env("GMAIL_ADDRESS", ""))
        password = ((_env("AVILX_SMTP_PASS")
                     or _env("SMTP_PASSWORD")
                     or _env("GMAIL_APP_PASSWORD", "")).replace(" ", ""))
        use_ssl = (_env("AVILX_SMTP_USE_SSL")
                   or _env("SMTP_USE_SSL", "true")).lower() == "true"

    return {
        "auth_mode": auth,
        "host": host,
        "port": port,
        "user": user,
        "password": password,
        "use_ssl": use_ssl,
    }


def describe(cfg: Optional[Dict[str, Any]] = None) -> str:
    """One-line description of the active send config (no secrets)."""
    c = cfg or smtp_config()
    return (f"{c['auth_mode']} auth via {c['host']}:{c['port']} "
            f"as {c['user'] or '(unset)'}"
            f"{' (SSL)' if c['use_ssl'] else ' (STARTTLS)'}")


# ──────────────────────────────────────────────────────────────────
# Session
# ──────────────────────────────────────────────────────────────────
@contextmanager
def open_smtp(cfg: Optional[Dict[str, Any]] = None) -> Iterator[smtplib.SMTP]:
    """Open an authenticated SMTP session.

    Yields the live SMTP object; the caller sends through it. Authentication
    happens before the session is yielded, so a bad token raises here rather
    than after the message has been assembled.
    """
    c = cfg or smtp_config()
    ctx = ssl.create_default_context()

    if c["auth_mode"] == "oauth2":
        ok, token = m365_auth.get_access_token()
        if not ok:
            raise RuntimeError(f"Microsoft 365 authentication failed: {token}")
        # Outlook SMTP AUTH: STARTTLS first, then the XOAUTH2 exchange.
        # smtplib has no built-in XOAUTH2 handler, so issue AUTH by hand.
        with smtplib.SMTP(c["host"], c["port"], timeout=30) as s:
            s.ehlo()
            s.starttls(context=ctx)
            s.ehlo()
            blob = m365_auth.build_xoauth2_blob(c["user"], token).decode("ascii")
            code, resp = s.docmd("AUTH", f"XOAUTH2 {blob}")
            if code != 235:
                raise smtplib.SMTPAuthenticationError(code, resp)
            yield s
        return

    if c["use_ssl"]:
        with smtplib.SMTP_SSL(c["host"], c["port"], context=ctx, timeout=30) as s:
            s.login(c["user"], c["password"])
            yield s
        return

    with smtplib.SMTP(c["host"], c["port"], timeout=30) as s:
        s.starttls(context=ctx)
        s.login(c["user"], c["password"])
        yield s


# ──────────────────────────────────────────────────────────────────
# Send
# ──────────────────────────────────────────────────────────────────
def send_via_config(msg: Any, envelope_from: str, envelope_to: str,
                    cfg: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Send one message through the configured session.

    Returns the refused-recipients dict from `send_message` (empty on
    success). Raises on auth or transport failure.
    """
    with open_smtp(cfg) as s:
        return s.send_message(msg, from_addr=envelope_from, to_addrs=[envelope_to])


def _is_permanent(exc: BaseException) -> bool:
    """True when the error must not be retried."""
    if isinstance(exc, smtplib.SMTPAuthenticationError):
        return True
    if isinstance(exc, (smtplib.SMTPRecipientsRefused, smtplib.SMTPSenderRefused)):
        return True
    if isinstance(exc, smtplib.SMTPResponseException):
        code = getattr(exc, "smtp_code", 0)
        if code == 535:
            # SMTP AUTH failed — bad token, wrong scope, revoked consent.
            return True
        if code == 550 and "5.7.1" in str(exc):
            # "Sender not authorized" — the mailbox isn't licensed for the
            # From address, or lacks Send As permission for it.
            return True
        return code not in TRANSIENT_CODES
    if isinstance(exc, (smtplib.SMTPServerDisconnected, smtplib.SMTPConnectError,
                        smtplib.SMTPHeloError, smtplib.SMTPDataError,
                        socket.timeout, ConnectionError, OSError)):
        return False
    if isinstance(exc, smtplib.SMTPException):
        # Anything else is a broad protocol failure — treat as transient.
        return False
    return True


def send_with_retry(msg: Any, envelope_from: str, envelope_to: str,
                    cfg: Optional[Dict[str, Any]] = None,
                    on_attempt=None) -> Dict[str, Any]:
    """Send one message, retrying transient failures.

    `on_attempt(attempt, sleep_seconds, error)` is an optional hook used for
    logging. The first attempt has no delay; the retries wait 30s then 120s.
    """
    last_err: Optional[BaseException] = None
    for attempt, sleep_s in enumerate(RETRY_BACKOFF, start=1):
        if sleep_s:
            time.sleep(sleep_s)
        try:
            return send_via_config(msg, envelope_from, envelope_to, cfg)
        except Exception as e:
            last_err = e
            if on_attempt:
                on_attempt(attempt, sleep_s, e)
            if _is_permanent(e) or attempt == len(RETRY_BACKOFF):
                break
    raise last_err  # type: ignore[misc]
