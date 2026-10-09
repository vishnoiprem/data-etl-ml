# Lesson 02 — OAuth and Multi-Tenancy

> **A single-tenant service can ship to 1 customer. A multi-tenant service can ship to 12.**

## 🎯 Outcome

By the end of this lesson you can:

1. Issue a JWT (RS256-signed) with a `tenant_id` claim.
2. Verify a JWT and resolve a tenant config from the token.
3. Explain why the `tenant_id` belongs in the **token**, not in the URL or header (URLs leak via logs; headers are spoofable from the client side).

## 🧠 Mindset

Phase 4 had 1 customer (PacificFreight). Phase 5 has 12 (PacificFreight + 11 e-commerce platforms that came over after the growth event). The drafter now serves 12 different policies, 12 different rate limits, 12 different cost ceilings.

The risk: Mei's token at PacificFreight shouldn't be able to call the refund endpoint at the e-commerce customer. **Tenant isolation is the #1 multi-tenant security boundary.**

The mechanism: every JWT has a `tenant_id` claim. Every data access is scoped to that tenant. A request with `tenant_id=pf` can ONLY read/write `pf/*` keys.

```
PacificFreight (Mei)             ECommercePlatform (Bob)
    Bearer eyJ...pf                  Bearer eyJ...ecom
         │                                  │
         ▼                                  ▼
    TenantResolver                  TenantResolver
         │                                  │
    policy=pf.yaml                  policy=ecom.yaml
    budget=$5/mo                     budget=$50/mo
    rate_limit=60/min                rate_limit=200/min
```

## 🛠️ Practice

Open `projects/02-oauth-multi-tenant/service/oauth.py`. The key bits:

1. **`OAuthProvider.issue()`** mints a JWT (RS256-signed) with `tenant_id + user_id + role`.
2. **`OAuthProvider.verify()`** checks the signature + expiration. Bad tokens raise `PermissionError`.
3. **`TenantResolver.resolve()`** parses the `Authorization: Bearer ...` header → `(TokenClaims, TenantConfig)`.

Run the demo:

```bash
cd projects/02-oauth-multi-tenant
pip install pyjwt cryptography
python3 service/oauth.py
```

Expected: 4 sections print (issue+verify, isolation, invalid token rejected, unknown tenant rejected).

Then the 3 tests:

```bash
python3 -m pytest phase-5-advanced/projects/02-oauth-multi-tenant/tests/test_oauth.py -v
```

Expected: **3 passed.**

## 🏛️ FDE Lens — the production reality underneath

| Decision | Choice | Why |
|---|---|---|
| **JWT algorithm** | RS256 (RSA) | Service holds public key only; auth server holds private key. A compromised service can't mint tokens. |
| **JWT lifetime** | 1 hour | Long enough for a CS user to work without re-auth; short enough to limit damage from a stolen token. |
| **Tenant claim location** | In the token (not the URL or header) | Token is signed; URL is logged; header is client-controlled. |
| **Tenant config storage** | YAML per tenant | Same reason as Phase 4 MCP: code-reviewable, version-controlled, diffable. |
| **Session store** | Redis (Phase 5 P1) | Token revocation must propagate; an in-process dict would let revoked tokens linger for up to 1 worker lifetime. |

**The migration is non-breaking.** Phase 4's `/draft` endpoint becomes Phase 5's `/draft` endpoint + a `TenantResolver` middleware. **The 13/13 Phase 3 tests still pass.**

## 🌙 Reflect

1. What's the difference between authentication (who are you) and authorization (what can you do)? Where does each live in this codebase?
2. Mei (PacificFreight, cs_junior) and Mei (ECommercePlatform, cs_junior) have the SAME role name. **What stops them from being interchanged?**
3. The `OAuthProvider` uses RS256. **Why is RS256 better than HS256 (HMAC) for a multi-service deployment?**
