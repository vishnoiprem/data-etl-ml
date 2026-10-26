"""
projects/02-oauth-multi-tenant/service/oauth.py — minimal OAuth + JWT for Phase 5.

What this file does
-------------------
1. **Issue JWTs** (RS256-signed) with a `tenant_id` claim.
2. **Verify JWTs** on every request.
3. **Resolve tenant** from the Authorization header.

The threat model is "a user at tenant A presenting a valid token for
tenant A, but trying to access tenant B's data." The fix: the JWT carries
a `tenant_id` claim, and every data access is scoped to that tenant_id.

Why RS256
---------
RS256 (RSA + SHA-256) lets us distribute only the public key to the
service. The private key (which signs tokens) lives on the auth server.
A compromised service can't mint tokens; it can only verify them.

In production we'd use a library like `python-jose` or `authlib`. For the
lesson, we use `pyjwt` + `cryptography` for minimal surface area.

How to run
----------
    pip install pyjwt cryptography
    python3 oauth.py
"""
from __future__ import annotations

import json
import os
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


# Lazy imports so the module loads even when pyjwt is missing
def _lazy_pyjwt():
    try:
        import jwt  # type: ignore
        return jwt
    except ImportError:
        raise ImportError(
            "oauth.py requires PyJWT: `pip install pyjwt cryptography`"
        )


def _lazy_crypto():
    try:
        from cryptography.hazmat.primitives import serialization  # type: ignore
        from cryptography.hazmat.primitives.asymmetric import rsa  # type: ignore
        return serialization, rsa
    except ImportError:
        raise ImportError(
            "oauth.py requires cryptography: `pip install pyjwt cryptography`"
        )


# ---------------------------------------------------------------------------
# Tenant config — maps tenant_id → policy YAML (the contract)
# ---------------------------------------------------------------------------
def _default_tenant_config() -> dict:
    """Default tenant config for the lesson. In production this is a
    YAML file per tenant in `tenants/{tenant_id}.yaml`."""
    return {
        "pf": {
            "name": "PacificFreight",
            "rate_limits": {"per_user_per_min": 60},
            "model": "gpt-4o-mini",
            "budget_usd_per_month": 5.0,
        },
        "ecom": {
            "name": "ECommercePlatform",
            "rate_limits": {"per_user_per_min": 200},
            "model": "gpt-4o-mini",
            "budget_usd_per_month": 50.0,
        },
    }


# ---------------------------------------------------------------------------
# Key management — generate an RSA keypair on first use; persist to disk
# ---------------------------------------------------------------------------
def _load_or_create_keypair(key_dir: Path) -> tuple:
    """Return (private_key, public_key) as PEM bytes. Persists to disk
    so tokens survive a restart."""
    priv_path = key_dir / "oauth_private.pem"
    pub_path = key_dir / "oauth_public.pem"
    if priv_path.exists() and pub_path.exists():
        return priv_path.read_bytes(), pub_path.read_bytes()
    serialization, rsa = _lazy_crypto()
    key_dir.mkdir(parents=True, exist_ok=True)
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    priv = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    pub = key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    priv_path.write_bytes(priv)
    pub_path.write_bytes(pub)
    return priv, pub


# ---------------------------------------------------------------------------
# The issuer + verifier
# ---------------------------------------------------------------------------
@dataclass
class TokenClaims:
    tenant_id: str
    user_id: str
    role: str
    issued_at: int
    expires_at: int

    def to_dict(self) -> dict:
        return {
            "tenant_id": self.tenant_id,
            "user_id": self.user_id,
            "role": self.role,
            "iat": self.issued_at,
            "exp": self.expires_at,
        }


class OAuthProvider:
    """The OAuth provider. Issues + verifies JWTs."""

    def __init__(
        self,
        *,
        key_dir: Optional[Path] = None,
        tenants: Optional[dict] = None,
        issuer: str = "pf-auth",
        audience: str = "pf-drafter",
    ) -> None:
        self.key_dir = key_dir or Path(".oauth_keys")
        self.priv, self.pub = _load_or_create_keypair(self.key_dir)
        self.tenants = tenants or _default_tenant_config()
        self.issuer = issuer
        self.audience = audience

    def issue(
        self,
        tenant_id: str,
        user_id: str,
        role: str,
        *,
        ttl_s: int = 3600,
    ) -> str:
        """Issue a JWT for the given tenant + user. Returns the encoded token."""
        if tenant_id not in self.tenants:
            raise ValueError(f"unknown tenant: {tenant_id!r}")
        now = int(time.time())
        claims = TokenClaims(
            tenant_id=tenant_id,
            user_id=user_id,
            role=role,
            issued_at=now,
            expires_at=now + ttl_s,
        )
        payload = claims.to_dict()
        # iss + aud are required claims for multi-tenant safety. The
        # verifier rejects any token that doesn't match self.issuer /
        # self.audience — see verify() below.
        payload["iss"] = self.issuer
        payload["aud"] = self.audience
        jwt = _lazy_pyjwt()
        return jwt.encode(payload, self.priv, algorithm="RS256")

    def verify(self, token: str) -> TokenClaims:
        """Verify the token signature + claims. Raises on any failure.

        Security-critical: we explicitly require `iss` and `aud` to match
        the configured values, and we require the four claims the rest of
        the service depends on (exp, iat, tenant_id, role). Without
        these checks, a token issued for any other tenant (or any other
        audience) would be accepted here — see the Phase 5 P2 lesson on
        OAuth + multi-tenancy for the threat model.
        """
        jwt = _lazy_pyjwt()
        try:
            payload = jwt.decode(
                token, self.pub, algorithms=["RS256"],
                issuer=self.issuer, audience=self.audience,
                options={"require": ["exp", "iat", "tenant_id", "role", "iss", "aud"]},
            )
        except Exception as e:
            raise PermissionError(f"token verification failed: {type(e).__name__}: {e}")
        return TokenClaims(
            tenant_id=payload["tenant_id"],
            user_id=payload["user_id"],
            role=payload["role"],
            issued_at=payload["iat"],
            expires_at=payload["exp"],
        )

    def tenant_config(self, tenant_id: str) -> dict:
        """Return the tenant's config block. Used by the policy middleware."""
        if tenant_id not in self.tenants:
            raise KeyError(f"unknown tenant: {tenant_id!r}")
        return self.tenants[tenant_id]


# ---------------------------------------------------------------------------
# Tenant resolver — the middleware
# ---------------------------------------------------------------------------
class TenantResolver:
    """A middleware-shaped helper that turns `Authorization: Bearer <token>`
    into a `(TokenClaims, TenantConfig)` pair. The drafter's handlers
    call `resolve(request)` instead of parsing headers themselves."""

    def __init__(self, provider: OAuthProvider) -> None:
        self.provider = provider

    def resolve(self, authorization_header: str) -> tuple:
        """Resolve an Authorization header to (claims, tenant_config)."""
        if not authorization_header or not authorization_header.startswith("Bearer "):
            raise PermissionError("missing or malformed Authorization header")
        token = authorization_header[len("Bearer "):].strip()
        claims = self.provider.verify(token)
        cfg = self.provider.tenant_config(claims.tenant_id)
        return claims, cfg


# ---------------------------------------------------------------------------
# CLI demo
# ---------------------------------------------------------------------------
def main() -> int:
    print("=" * 70)
    print("OAuth — Phase 5 Project 2 (multi-tenant)")
    print("=" * 70)

    p = OAuthProvider(key_dir=Path(".oauth_keys_demo"))
    resolver = TenantResolver(p)

    print("\n--- 1. issue + verify at tenant=pf ---")
    token = p.issue("pf", "mei@pf.com", "cs_senior")
    claims, cfg = resolver.resolve(f"Bearer {token}")
    print(f"  claims = {claims}")
    print(f"  cfg    = {cfg['name']} | model={cfg['model']} | budget=${cfg['budget_usd_per_month']}/mo")

    print("\n--- 2. issue at ecom, verify isolation ---")
    token_a = p.issue("pf", "mei@pf.com", "cs_senior")
    token_b = p.issue("ecom", "evil@ecom.com", "cs_junior")
    claims_a, _ = resolver.resolve(f"Bearer {token_a}")
    claims_b, cfg_b = resolver.resolve(f"Bearer {token_b}")
    print(f"  pf claims   = tenant={claims_a.tenant_id}, role={claims_a.role}")
    print(f"  ecom claims = tenant={claims_b.tenant_id}, role={claims_b.role}")
    print(f"  ecom cfg    = model={cfg_b['model']} | budget=${cfg_b['budget_usd_per_month']}/mo")
    assert claims_a.tenant_id != claims_b.tenant_id

    print("\n--- 3. invalid token rejected ---")
    try:
        resolver.resolve("Bearer fake-token-12345")
        print("  FAIL: should have raised")
    except PermissionError as e:
        print(f"  PASS: rejected with {e}")

    print("\n--- 4. unknown tenant rejected ---")
    try:
        p.issue("made-up-tenant", "x@y.z", "cs_junior")
        print("  FAIL: should have raised")
    except ValueError as e:
        print(f"  PASS: rejected with {e}")

    print("\n" + "=" * 70)
    print("DEMO COMPLETE")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
