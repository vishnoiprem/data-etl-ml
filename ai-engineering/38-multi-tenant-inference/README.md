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

**Last updated:** 2026-10-12  
**License:** MIT — use freely in your own courses, prototypes, and products.  
