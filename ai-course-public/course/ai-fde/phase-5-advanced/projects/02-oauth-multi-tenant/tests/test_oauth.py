"""
projects/02-oauth-multi-tenant/tests/test_oauth.py — 3 tests for OAuth + tenant.

1. test_issue_and_verify        — round-trip a token
2. test_tenant_isolation        — tenant A can't mint for tenant B
3. test_unknown_tenant_rejected — issuing for unknown tenant raises
"""
from __future__ import annotations

import sys
from pathlib import Path

SVC = Path(__file__).parent.parent / "service"
sys.path.insert(0, str(SVC))

from oauth import OAuthProvider, TenantResolver  # noqa: E402


def _provider():
    """Create a provider with a fresh key pair in a tmp dir."""
    import tempfile
    d = Path(tempfile.mkdtemp(prefix="oauth_test_"))
    return OAuthProvider(key_dir=d), d


def test_issue_and_verify():
    p, d = _provider()
    resolver = TenantResolver(p)
    token = p.issue("pf", "mei@pf.com", "cs_senior")
    claims, cfg = resolver.resolve(f"Bearer {token}")
    assert claims.tenant_id == "pf"
    assert claims.user_id == "mei@pf.com"
    assert claims.role == "cs_senior"
    assert cfg["name"] == "PacificFreight"
    print(f"  PASS: round-trip OK; cfg.name={cfg['name']}")


def test_tenant_isolation():
    p, d = _provider()
    resolver = TenantResolver(p)
    token_a = p.issue("pf", "alice@pf.com", "cs_senior")
    token_b = p.issue("ecom", "bob@ecom.com", "cs_junior")
    ca, _ = resolver.resolve(f"Bearer {token_a}")
    cb, cb_cfg = resolver.resolve(f"Bearer {token_b}")
    assert ca.tenant_id == "pf" and cb.tenant_id == "ecom"
    # Budgets differ between tenants
    assert cb_cfg["budget_usd_per_month"] == 50.0  # ecom
    print(f"  PASS: pf/eu tenant isolated; ecom budget=${cb_cfg['budget_usd_per_month']}/mo")


def test_unknown_tenant_rejected():
    p, d = _provider()
    try:
        p.issue("made-up-tenant", "x@y.z", "cs_junior")
    except ValueError as e:
        assert "unknown tenant" in str(e).lower()
        print(f"  PASS: rejected with {e}")
        return
    raise AssertionError("should have raised ValueError")


def _run_all():
    print("=" * 60)
    print("OAuth tests — Phase 5 Project 2")
    print("=" * 60)
    for fn in [test_issue_and_verify, test_tenant_isolation, test_unknown_tenant_rejected]:
        print(f"\n[{fn.__name__}]")
        fn()
    print("\n" + "=" * 60)
    print("ALL 3 OAUTH TESTS PASSED")
    print("=" * 60)


if __name__ == "__main__":
    _run_all()
