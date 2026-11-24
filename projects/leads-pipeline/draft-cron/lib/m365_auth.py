"""
lib/m365_auth.py — Microsoft 365 (Outlook) OAuth2 token handling for SMTP AUTH.

Why this exists
---------------
The pipeline wants to send as `alex.morgan@avilx.com`. Gmail physically cannot
do that: it accepts `MAIL FROM:<alex.morgan@avilx.com>` with `250 2.1.0 OK`
but rewrites the delivered `From:` header to the login address, keeping the
original only in `X-Google-Original-From:`. Verified empirically on
2026-11-23.

`avilx.com` is already a Microsoft 365 tenant (MX points at
`avilx-com.mail.protection.outlook.com`, DKIM selectors 1 and 2 are live,
DMARC is `p=quarantine`), so the correct fix is Outlook **SMTP AUTH** —
OAuth2 with the XOAUTH2 SASL mechanism — not a third-party provider.

Outlook's SMTP AUTH accepts two SASL mechanisms: `PLAIN` (login/password,
deprecating) and `XOAUTH2` (bearer token). We use XOAUTH2 because it is
passwordless and supports refresh tokens.

How XOAUTH2 works
-----------------
The client base64-encodes this exact byte string and hands it to the server
as the SASL initial response:

    user=<mailbox>\x01auth=Bearer <access_token>\x01\x01

`\x01` is a literal 0x01 byte, not the two-character string `^A`. A wrong
separator is the classic silent failure here — the server rejects the auth
with a bare `535`, so `build_xoauth2_blob()` gets its own unit test.

Token lifecycle
---------------
1. **Bootstrap** — `python -m lib.m365_auth --device-code`. The device-code
   flow needs no browser redirect URI and no secret on the device, so it is
   the simplest path on a laptop. It yields an access token *and* a refresh
   token.
2. **Cache** — the token payload is written to `state/m365_token.json`
   (mode 0600) with its absolute expiry.
3. **Refresh** — on every send we check the cache. An unexpired access token
   is used directly; an expired one is refreshed with the refresh token
   (the `offline_access` scope is what makes refresh tokens possible).

Design notes
------------
- **No `msal` dependency.** The three HTTP calls (device code, poll, refresh)
  are small and `requests` is already a runtime dependency. Adding a package
  to CI for this would cost more than it saves.
- **`requests` is imported lazily inside the functions**, inside a
  `try/except`, so this module still imports (and the rest of the pipeline
  still runs on the Gmail path) when `requests` is unavailable. Same
  fail-open posture as `lib/email_guard.py`.
- **No `load_dotenv` here.** `lib/` modules read the environment; the entry
  points load `.env`. Mixing the two makes the token path unpredictable
  when a script is invoked from a different cwd.
- Every public function returns `(ok, value)` or raises only on programmer
  error. Failures that an operator can act on come back as a message.

CLI
---
    python -m lib.m365_auth --device-code   # bootstrap / re-consent
    python -m lib.m365_auth --status        # show cached token state
    python -m lib.m365_auth --clear         # delete the cached token
"""

from __future__ import annotations

import base64
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

HERE = Path(__file__).resolve().parent
PROJECT_ROOT = HERE.parent

# The scope Outlook SMTP AUTH requires. `offline_access` is what produces a
# refresh token — without it the cached token dies after ~1h and the
# pipeline can no longer send unattended.
XOAUTH2_SCOPE = "https://outlook.office.com/SMTP.Send offline_access"

# Default tenant for the avilx.com tenant.
DEFAULT_TENANT = "NETORGFT20933709.onmicrosoft.com"

LOGIN_BASE = "https://login.microsoftonline.com"

# Where the cached token lives. Override with AVILX_M365_TOKEN_PATH.
DEFAULT_TOKEN_PATH = PROJECT_ROOT / "state" / "m365_token.json"

# Treat a token as expired this many seconds early so we never hand the SMTP
# server a token that expires mid-handshake.
_EXPIRY_SKEW_SEC = 60


# ──────────────────────────────────────────────────────────────────
# Config
# ──────────────────────────────────────────────────────────────────
def _env(name: str, default: str = "") -> str:
    return (os.getenv(name, default) or "").strip()


def client_id() -> str:
    """Application (client) ID of the Entra app registration."""
    return _env("AVILX_M365_CLIENT_ID")


def client_secret() -> str:
    """Client secret of the Entra app registration."""
    return _env("AVILX_M365_CLIENT_SECRET")


def tenant_id() -> str:
    """Directory (tenant) ID of the avilx.com tenant."""
    return _env("AVILX_M365_TENANT_ID", DEFAULT_TENANT)


def sender() -> str:
    """The mailbox the pipeline authenticates as.

    Outlook SMTP AUTH only permits sending as the authenticated mailbox (or
    an address it has explicit Send As permission for). If this is only an
    alias, sends fail with `550 5.7.1 ... not authorized`.
    """
    return _env("AVILX_M365_SENDER") or _env("AVILX_FROM_EMAIL", "alex.morgan@avilx.com")


def token_path() -> Path:
    """Path of the cached token JSON."""
    raw = _env("AVILX_M365_TOKEN_PATH")
    p = Path(raw) if raw else DEFAULT_TOKEN_PATH
    if not p.is_absolute():
        p = PROJECT_ROOT / p
    return p


# ──────────────────────────────────────────────────────────────────
# XOAUTH2 SASL
# ──────────────────────────────────────────────────────────────────
def build_xoauth2_blob(user: str, access_token: str) -> bytes:
    """Build the base64 XOAUTH2 initial response for the SMTP AUTH command.

    The wire format is:

        base64("user=" + user + chr(1) + "auth=Bearer " + token + chr(1) + chr(1))

    Returns the *encoded* bytes, ready to be appended to the `AUTH XOAUTH2`
    command line.
    """
    raw = b"user=" + user.encode("utf-8") + b"\x01auth=Bearer " + access_token.encode("utf-8") + b"\x01\x01"
    return base64.b64encode(raw)


def build_xoauth2_initial_response(user: str, access_token: str) -> str:
    """The full argument string for `AUTH XOAUTH2 <this>`."""
    return "XOAUTH2 " + build_xoauth2_blob(user, access_token).decode("ascii")


# ──────────────────────────────────────────────────────────────────
# Token cache
# ──────────────────────────────────────────────────────────────────
def _read_cache(path: Optional[Path] = None) -> Optional[Dict[str, Any]]:
    """Read the cached token payload, or None if there isn't a usable one."""
    p = path or token_path()
    try:
        with open(p, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return None
    if not isinstance(data, dict):
        return None
    return data


def _write_cache(payload: Dict[str, Any], path: Optional[Path] = None) -> Path:
    """Write the token payload with 0600 permissions."""
    p = path or token_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)
    try:
        os.chmod(p, 0o600)
    except OSError:
        pass
    return p


def clear_cache(path: Optional[Path] = None) -> bool:
    """Delete the cached token. Returns True if a file was removed."""
    p = path or token_path()
    try:
        p.unlink()
        return True
    except (FileNotFoundError, OSError):
        return False


def _post_form(url: str, data: Dict[str, str], timeout: int = 30) -> Tuple[bool, Dict[str, Any]]:
    """POST a form-encoded body. Returns (ok, parsed_json).

    `requests` is imported lazily so this module imports cleanly without it.
    """
    try:
        import requests  # noqa: PLC0415 — lazy on purpose, see module docstring
    except ImportError:
        return False, {"error": "the 'requests' package is not installed (pip install requests)"}
    try:
        resp = requests.post(url, data=data, timeout=timeout)
    except Exception as e:  # network error — requests raises many types
        return False, {"error": f"token request failed: {e}"}
    try:
        body = resp.json()
    except ValueError:
        body = {"error": (resp.text or "")[:400]}
    if resp.status_code >= 400:
        return False, body
    return True, body


# ──────────────────────────────────────────────────────────────────
# Refresh
# ──────────────────────────────────────────────────────────────────
def _refresh_with_refresh_token(refresh_token: str, path: Optional[Path] = None) -> Tuple[bool, str]:
    """Exchange a refresh token for a fresh access token.

    Returns (ok, access_token_or_message).
    """
    cid, secret = client_id(), client_secret()
    if not cid or not secret:
        return False, ("AVILX_M365_CLIENT_ID / AVILX_M365_CLIENT_SECRET not set in .env "
                       "— run: python -m lib.m365_auth --device-code")

    url = f"{LOGIN_BASE}/{tenant_id()}/oauth2/v2.0/token"
    data = {
        "client_id": cid,
        "client_secret": secret,
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "scope": XOAUTH2_SCOPE,
    }
    ok, body = _post_form(url, data)
    if not ok:
        err = body.get("error_description") or body.get("error") or "unknown error"
        return False, f"token refresh failed: {err}"

    access = body.get("access_token") or ""
    if not access:
        return False, "token refresh returned no access_token"

    payload = {
        "access_token": access,
        "refresh_token": body.get("refresh_token") or refresh_token,
        "expires_at": time.time() + float(body.get("expires_in") or 3600),
        "scope": body.get("scope") or XOAUTH2_SCOPE,
    }
    _write_cache(payload, path)
    return True, access


def get_access_token(force_refresh: bool = False, path: Optional[Path] = None) -> Tuple[bool, str]:
    """Return (ok, access_token_or_message).

    Order:
      1. cached access token that is still valid → use it (no network call)
      2. cached refresh token → refresh, cache the result
      3. nothing usable → (False, message pointing at the device-code command)
    """
    cached = _read_cache(path)
    if cached:
        access = cached.get("access_token") or ""
        expires_at = float(cached.get("expires_at") or 0)
        fresh = access and (expires_at - _EXPIRY_SKEW_SEC) > time.time()
        if fresh and not force_refresh:
            return True, access
        refresh = cached.get("refresh_token") or ""
        if refresh:
            ok, result = _refresh_with_refresh_token(refresh, path)
            if ok:
                return True, result
            # A failed refresh usually means the consent was revoked or the
            # secret rotated. Clear the dead cache so the next run doesn't
            # keep retrying it.
            clear_cache(path)
            return False, (f"{result}. Re-run: python -m lib.m365_auth --device-code")
    return False, ("no Microsoft 365 token cached — run: "
                   "python -m lib.m365_auth --device-code")


def token_status(path: Optional[Path] = None) -> str:
    """Human-readable status of the cached token."""
    cached = _read_cache(path)
    if not cached:
        return "no token cached — run: python -m lib.m365_auth --device-code"
    expires_at = float(cached.get("expires_at") or 0)
    if expires_at <= 0:
        return "token cached (no expiry recorded)"
    remaining = expires_at - time.time()
    if remaining <= 0:
        return "token cached but EXPIRED (a refresh token is present, it will refresh on next send)"
    return f"token cached, valid for another {int(remaining // 60)} min"


# ──────────────────────────────────────────────────────────────────
# Device-code flow
# ──────────────────────────────────────────────────────────────────
def device_code_login(path: Optional[Path] = None) -> Tuple[bool, str]:
    """Run the OAuth2 device-code flow. Returns (ok, message).

    Prints the verification URL and user code, then polls until the user
    consents or the code expires.
    """
    cid = client_id()
    if not cid:
        return False, ("AVILX_M365_CLIENT_ID not set in .env — register the Entra app first "
                       "(see SETUP_OUTLOOK_SMTP.md)")

    url = f"{LOGIN_BASE}/{tenant_id()}/oauth2/v2.0/devicecode"
    ok, body = _post_form(url, {"client_id": cid, "scope": XOAUTH2_SCOPE})
    if not ok:
        err = body.get("error_description") or body.get("error") or "unknown error"
        return False, f"device code request failed: {err}"

    device_code = body.get("device_code") or ""
    user_code = body.get("user_code") or ""
    verify_uri = body.get("verification_uri") or body.get("verification_uri_complete") or ""
    interval = int(body.get("interval") or 5)
    expires_in = int(body.get("expires_in") or 900)

    if not device_code:
        return False, "device code request returned no device_code"

    print("\n  Open this URL and sign in as the sending mailbox:\n")
    print(f"      {verify_uri}")
    print(f"\n  Enter the code: {user_code}\n")
    print(f"  Waiting for consent (expires in {expires_in // 60} min)...\n", flush=True)

    token_url = f"{LOGIN_BASE}/{tenant_id()}/oauth2/v2.0/token"
    deadline = time.time() + expires_in
    while time.time() < deadline:
        time.sleep(interval)
        ok, tok = _post_form(token_url, {
            "client_id": cid,
            "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
            "device_code": device_code,
        })
        if ok:
            access = tok.get("access_token") or ""
            if not access:
                return False, "token response contained no access_token"
            payload = {
                "access_token": access,
                "refresh_token": tok.get("refresh_token") or "",
                "expires_at": time.time() + float(tok.get("expires_in") or 3600),
                "scope": tok.get("scope") or XOAUTH2_SCOPE,
            }
            saved = _write_cache(payload, path)
            return True, f"token cached at {saved}"
        err = tok.get("error") or ""
        if err == "authorization_pending":
            continue
        if err == "slow_down":
            interval += 5
            continue
        if err == "expired_token":
            return False, "the device code expired — run the command again"
        desc = tok.get("error_description") or err or "unknown error"
        return False, f"device code flow failed: {desc}"

    return False, "the device code expired before consent — run the command again"


# ──────────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────────
def main(argv: Optional[list] = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if "--clear" in args:
        removed = clear_cache()
        print(f"  {'removed' if removed else 'no'} token cache at {token_path()}")
        return 0
    if "--device-code" in args:
        ok, msg = device_code_login()
        print(f"  {'✅' if ok else '❌'} {msg}")
        return 0 if ok else 1
    # default: status
    print(f"  tenant: {tenant_id()}")
    print(f"  client: {client_id() or '(not set)'}")
    print(f"  sender: {sender()}")
    print(f"  cache:  {token_path()}")
    print(f"  {token_status()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
