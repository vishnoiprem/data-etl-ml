# OpenAI / Anthropic-style multi-tenant inference gateway

Per-tenant routing, cost attribution that lands in the same dashboard as p95 latency, prompt versioning, and per-tenant rate limits so one team can't starve the others. The toy captures the gateway decision logic; the real platform wraps it with auth, billing, and observability.

## Shape

```
   request: { tenant_id, prompt_tokens, expected_output_tokens, model }
                     │
                     ▼
        ┌────────────────────────┐
        │  MultiTenantGateway    │
        │   .allow(req)          │
        └────────┬───────────────┘
                 │
   ┌─────────────┼──────────────┐
   ▼             ▼              ▼
  rate-limit   daily-budget   tenant-status
  (sliding     (token budget  (allowed / disabled)
   window)     per tenant)
   │             │              │
   └──────┬──────┴──────────────┘
          ▼
     Decision(allowed, reason)
          │
          ▼
     proceed to inference
```

## What I built

- `gw/gateway.py` — `Tenant` (rate_limit_rpm, daily_token_budget, spent_tokens_today) + `InferenceRequest` + `MultiTenantGateway`.
- `allow()` checks 3 things in order: tenant exists + is enabled, rate limit (sliding 60s window), daily budget.
- `_window[tenant_id]` is a deque of timestamps in the last 60 seconds — pruned on every check.
- `report()` shows per-tenant usage: rpm used / limit, tokens used today / budget.
- Smoke test: 2 tenants with different limits, team-A exhausts rate limit, team-B comes in fresh, team-A over-spends daily budget.

## Real numbers

- Rate limit window: 60s sliding window. Token-bucket alternative: 1s granularity, smoother but harder to reason about.
- Daily budget: 1M tokens for a small team, 100M+ for a heavy user. Reset at midnight UTC, not per-tenant-local.
- Cost attribution: per-token `cost_per_1k` summed at the gateway, lands in the same dashboard as p95 latency.
- 429 vs 402: rate-limit returns 429 (transient, retry later), budget returns 402 (payment required, no retry).

## What I learned the hard way

- **Per-tenant limits are fairness, not just budget.** One team that hits the API 1000x/min will starve everyone else. The rate limit is what protects your other customers.
- **Daily budgets are negotiated, not enforced.** A 402 mid-month is a failure; you should warn at 80% and 95% via email/Slack before the user hits the wall.
- **Tenant-disabled is a power tool.** A single tenant that gets compromised or goes rogue can be flipped off in 30s without affecting the rest.
- **The report is the product.** A gateway that limits but doesn't report is a billing mystery. Surface the usage to the tenant; they self-throttle.

## When to use

- You're serving more than 1 team on the same inference pool.
- You have multi-tenant fairness concerns.
- You need cost attribution per team per model.

## When NOT to use

- Single-tenant serving (no fairness to enforce).
- Internal-only tools where the cost is a fixed line item.

## Run

```bash
pip install -r requirements.txt
make smoke
```

---

## What this is NOT

- **Not OpenAI / Anthropic.** Those are the
  closed-weights API providers; their
  multi-tenant gateway is the production version
  of this pattern. This is the *allow()
  decision* in ~100 lines.
- **Not a billing system.** The gateway knows
  the *budget*; it doesn't issue invoices. The
  billing integration (Stripe, invoicing, dunning)
  is a separate system that consumes the per-tenant
  usage report.
- **Not an auth layer.** The `tenant_id` is
  assumed; the gateway doesn't verify the
  caller. Pair it with an auth middleware (JWT
  verification, API key check) before the
  gateway in the request path.
- **Not a substitute for the per-request budget
  guard.** The per-tenant daily budget is
  *cumulative*; the per-request budget guard
  (in
  [`../26-mistral-self-host/`](../26-mistral-self-host/))
  is *per-call*. They protect against different
  failure modes — one tenant with a 200K-context
  paste (per-request) vs one team that slowly
  burns through the daily budget (per-tenant).
  You need both.

---

## Related directories

- [`../24-vertex-style-platform/`](../24-vertex-style-platform/) —
  the multi-backend gateway that this per-tenant
  fairness layer builds on top of.
- [`../26-mistral-self-host/`](../26-mistral-self-host/) —
  the per-request budget guard that complements
  this per-tenant cumulative limit.
- [`../36-together-gpu-cloud/`](../36-together-gpu-cloud/) —
  the GPU pool / autoscaler that the per-tenant
  load shaping feeds into.
- [`../../data-engineering/multi-tenant-isolation/`](../../data-engineering/multi-tenant-isolation/) —
  the broader multi-tenant patterns (Postgres
  RLS, per-tenant keys) that the tenant-id
  here assumes.

---

**Last updated:** 2026-10-12  
**License:** MIT — use freely in your own courses, prototypes, and products.  
