"""Authentication for the Graph RAG API.

JWT in an HttpOnly cookie.  Users live in ClickHouse (table `users`).
Default admin:  admin / admin   (override via env: ADMIN_USERNAME, ADMIN_PASSWORD)

If a real production deployment, replace `ensure_default_admin` and the
password verification with a proper IdP / Cognito / Auth0.  The endpoint
shape stays the same.
"""
from __future__ import annotations

import os
import secrets
import time
from dataclasses import dataclass

import bcrypt  # type: ignore
from fastapi import Cookie, Depends, HTTPException, Response, status
from jose import JWTError, jwt  # type: ignore
from loguru import logger

# NOTE: We intentionally do NOT import `ch` from api.app.main at module
# load — that creates a circular import.  Callers pass the CHClient or
# use `get_ch()` to fetch the live one.


# ─────────────────────────────────────────────────────────────────────────────
# Config
# ─────────────────────────────────────────────────────────────────────────────

JWT_SECRET = os.environ.get("JWT_SECRET") or secrets.token_urlsafe(48)
JWT_ALG = "HS256"
JWT_TTL_SECONDS = 60 * 60 * 8  # 8h
COOKIE_NAME = "grag_session"


# ─────────────────────────────────────────────────────────────────────────────
# User store
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class User:
    username: str
    display_name: str
    role: str  # 'user' | 'admin'


def _hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def _verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode(), hashed.encode())
    except Exception:
        return False


def ensure_default_admin() -> None:
    """Insert the default admin if no users exist yet."""
    assert ch is not None
    rows = ch.query_df("SELECT count() AS n FROM graph_rag.users")
    n = int(rows[0]["n"]) if rows else 0
    if n > 0:
        return
    admin_user = os.environ.get("ADMIN_USERNAME", "admin")
    admin_pass = os.environ.get("ADMIN_PASSWORD", "admin")
    ch.insert_dicts(
        "users",
        [
            {
                "username": admin_user,
                "password_hash": _hash_password(admin_pass),
                "display_name": "Admin",
                "role": "admin",
            }
        ],
    )
    logger.info(f"Default admin created: {admin_user!r} (change the password!)")


def find_user(username: str) -> tuple[str, str, str, str] | None:
    """Return (username, password_hash, display_name, role) or None."""
    assert ch is not None
    rows = ch.query_df(
        f"SELECT username, password_hash, display_name, role "
        f"FROM graph_rag.users FINAL WHERE username = '{username.replace(chr(39), chr(39)*2)}' "
        f"LIMIT 1"
    )
    if not rows:
        return None
    r = rows[0]
    return r["username"], r["password_hash"], r["display_name"], r["role"]


def register_user(username: str, password: str, display_name: str = "", role: str = "user") -> None:
    assert ch is not None
    ch.insert_dicts(
        "users",
        [
            {
                "username": username,
                "password_hash": _hash_password(password),
                "display_name": display_name or username,
                "role": role,
            }
        ],
    )


def update_last_login(username: str) -> None:
    assert ch is not None
    # ClickHouse doesn't have UPDATE; we use ReplacingMergeTree and re-insert
    rows = ch.query_df(
        f"SELECT username, password_hash, display_name, role FROM graph_rag.users FINAL WHERE username = '{username}'"
    )
    if not rows:
        return
    r = rows[0]
    ch.insert_dicts(
        "users",
        [
            {
                "username": r["username"],
                "password_hash": r["password_hash"],
                "display_name": r["display_name"],
                "role": r["role"],
                "created_at": r.get("created_at"),
                "last_login_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            }
        ],
    )


# ─────────────────────────────────────────────────────────────────────────────
# JWT
# ─────────────────────────────────────────────────────────────────────────────

def issue_token(user: User) -> str:
    now = int(time.time())
    payload = {
        "sub": user.username,
        "name": user.display_name,
        "role": user.role,
        "iat": now,
        "exp": now + JWT_TTL_SECONDS,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)


def decode_token(token: str) -> User | None:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
        return User(
            username=payload["sub"],
            display_name=payload.get("name", payload["sub"]),
            role=payload.get("role", "user"),
        )
    except JWTError:
        return None


# ─────────────────────────────────────────────────────────────────────────────
# FastAPI dependency
# ─────────────────────────────────────────────────────────────────────────────

def get_current_user(grag_session: str | None = Cookie(default=None)) -> User:
    if not grag_session:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")
    user = decode_token(grag_session)
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired session")
    return user


def set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        max_age=JWT_TTL_SECONDS,
        httponly=True,
        samesite="lax",
        # secure=True in production (HTTPS)
    )


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(COOKIE_NAME)
