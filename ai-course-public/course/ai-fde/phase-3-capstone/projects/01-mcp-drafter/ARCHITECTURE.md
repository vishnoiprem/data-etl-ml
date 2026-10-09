# Project 1 — MCP-tooled drafter (Architecture)

> **Phase 4, Project 1.** Extends the Phase 3 PacificFreight drafter with 4 MCP-callable tools (tracker, refund, translate, escalate) gated by a YAML policy file.

## 1. System diagram

```
                         PacificFreight CS team
                                  │
                                  │  POST /draft  (email body)
                                  ▼
                  ┌─────────────────────────────────┐
                  │  service/app.py  (Phase 3)      │
                  │  /draft  +  /draft/stream       │
                  │  ─────────────────────────────  │
                  │  + /mcp/tools (Phase 4 NEW)     │
                  └────────────┬────────────────────┘
                               │
                ┌──────────────┼──────────────┐
                │              │              │
                ▼              ▼              ▼
        HybridRetriever   CircuitBreaker   Redactor
        (Phase 3)         + RateLimiter    (Phase 3)
                          (Phase 3)
                │              │              │
                ▼              ▼              ▼
         Top-K chunks    LLM call (or     "[REDACTED:..]"
                         tool call)        in the prompt
                               │
                               │  if drafter emits tool_call:
                               ▼
                  ┌─────────────────────────────────┐
                  │  mcp_server.py  (Phase 4 NEW)   │
                  │  ─────────────────────────────  │
                  │  • tracker.lookup               │
                  │  • refund.create                │
                  │  • translate.to                 │
                  │  • escalate.to_human            │
                  │                                 │
                  │  Enforces mcp_policies.yaml:    │
                  │   - role-based access (RBAC)    │
                  │   - per-tool rate limit         │
                  │   - unified credit budget       │
                  └────────────┬────────────────────┘
                               │
                               ▼
                        tool result →
                        fed back into the prompt
                               │
                               ▼
                  ┌─────────────────────────────────┐
                  │  Drafter produces the           │
                  │  final reply (Phase 3)          │
                  └─────────────────────────────────┘
```

The MCP server is a **sidecar process** in production. The drafter (Phase 3) talks to it over HTTP. A failure of the MCP server does NOT take down the drafter — the drafter falls back to free-text drafts (the Phase 3 3-tier fallback pattern).

## 2. Component choices

| Component | Choice | Why |
|---|---|---|
| Wire format | JSON-RPC 2.0 | MCP's standard transport. Stable. Tooling exists. |
| Policy file | YAML | Human-editable; reviewed by Daniel; one file = one contract. No code change to add a role or tool. |
| RBAC | Role-based, deny-by-default | Mei is `cs_junior`; Alice (senior) is `cs_senior`; Sarah is `ops`; Daniel is `it`. The 5 roles cover the PF org. |
| Rate limit | Per-user sliding window, unified budget | One number to reason about (60 credits/min). The policy file is the source of truth. |
| Per-tool cost | `cost_credits` field in the policy | A `refund.create` is 10× more expensive than a `tracker.lookup` in terms of finance-system impact. The credit system encodes that. |
| State | In-process dict | Phase 4 has no Redis. The rate limiter is per-process. Phase 5 (production) swaps to Redis Lua. |
| Failure mode | Drafter falls back to free-text | The Phase 3 3-tier fallback pattern. Mei still gets a reply, just without the tool result. |

## 3. Capacity model

| Metric | Phase 3 baseline | Phase 4 with MCP | Notes |
|---|---|---|---|
| Throughput | 150 drafts/day | 150 drafts/day + ~50 tool calls/day | Most drafts don't need tools. |
| Latency | P95 1.8s | P95 2.5s (tool call adds ~700ms) | The MCP server is local (same VM). |
| Cost | $0.50/week | $0.55/week (tool calls add ~$0.05) | The tool calls are local; only the LLM costs money. |
| Storage | 22 chunks in policy | 22 chunks + 4 tool schemas | Trivial. |
| Failure modes | LLM down → stub | LLM down → stub; MCP down → free-text fallback | The drafter survives any single component failure. |

## 4. Cost model

Per-tool cost in **cents** (USD, based on PF's $0.0005/draft + the tool overhead):

| Tool | Cost credits | Equiv. cents | Notes |
|---|---|---|---|
| `tracker.lookup` | 1 | ~$0.0001 | Local file read. |
| `refund.create` | 10 | ~$0.001 | Would call finance system in prod. |
| `translate.to` | 5 | ~$0.0005 | Mock translate in Phase 4. Real = $0.001. |
| `escalate.to_human` | 1 | ~$0.0001 | Slack notification. |

A `cs_senior` user can issue up to 6 refunds/min before hitting the budget. The unified budget is 60 credits/min — the cap on tool-call impact.

## 5. Failure modes

| Failure | Detection | Mitigation | Recovery |
|---|---|---|---|
| MCP server is down | HTTP timeout on `/mcp/tools` (5s) | Drafter falls back to free-text draft | Log to `usage.jsonl` with `outcome=mcp_unavailable`; alert Daniel after 5 in 10 min |
| Tool raises an exception | Caught in `_tool_*` | Returns 500 with the error | Tool result is treated as empty; drafter still replies |
| Policy file is malformed | `yaml.safe_load` raises | Default policies in code | Log warning; the drafter uses defaults |
| Rate limit hit | 429 response | Return 429; drafter skips the tool call | Log to `usage.jsonl` with `outcome=rate_limited` |
| RBAC violation | 403 response | Drafter returns "I can't do that — talk to a senior" | Log with `user_id` + `role` for audit |

## 6. Security policy

- **Inputs are validated** against the JSON schema. The drafter cannot call a tool with invalid args.
- **PII is stripped** by Phase 3's `Redactor` BEFORE the LLM emits a tool call. The tool never sees raw email text — only the parsed arguments.
- **RBAC is enforced** at the MCP server, not at the drafter. A compromised drafter cannot bypass the policy.
- **Audit trail** is in `usage.jsonl`: every tool call records `user_id`, `role`, `tool_name`, `cost_credits`, `latency_ms`, `outcome`.
- **Rate limit per user** prevents a single CS user from accidentally issuing 1000 refunds in 10 minutes.

## 7. What this project proves

Phase 3's drafter is a single-purpose LLM call. The MCP lift turns it into a **tool-using agent** that respects the same operational boundaries (rate limit, breaker, redaction) as before. The cost ceiling now applies to tool calls too, not just LLM tokens.

The lesson is: **the policy file is the contract.** The drafter's behavior is constrained by what's in the YAML. A new role is a 1-line addition. A new tool is 30 lines of code + 1 paragraph in the YAML. The drafter doesn't change.
