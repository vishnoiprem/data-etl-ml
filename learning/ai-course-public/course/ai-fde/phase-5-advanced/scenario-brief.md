# Scenario Lift — Phase 4 → Phase 5

> **The customer grew. The system has to grow with them.**

---

## Where Phase 4 left us

End of Phase 4, PacificFreight Co.:

- 12-person SMB; Mei sends 150 drafts/day through the drafter; thumbs-up 82%; P95 1.8s; cost $0.18/wk (post-SLM).
- 13/13 Phase 3 tests + 12/12 Phase 4 tests = 25/25 green.
- 5-question handoff test passed at 30/60/90 days. Mei, Sarah, Daniel all run the Monday cadence.
- The Phase 4 lifts (MCP, multi-agent, SLM, data analyst) run as sidecars to the Phase 3 FastAPI service.
- Single VM (2 vCPU / 4 GB / $15/mo) in Singapore. One uvicorn worker. One Redis instance would be over-provisioned.

**Then PacificFreight grew.** Their biggest customer (a 50-person e-commerce platform in Vietnam) switched to PacificFreight's logistics services after a competitor outage. Mei's CS team grew from 1 to 12. Volume grew from 150 to 15,000 drafts/day (100× growth). The single-VM FastAPI service is now the bottleneck.

The CEO called the FDE on a Friday at 5pm: "We grew overnight. The drafter is choking. The cost ceiling is going to blow. We need it fixed by Monday."

**This is exactly the moment Phase 5 is for.**

---

## The 100× growth problem

The single VM that served 150 drafts/day was fine. At 15,000 drafts/day, four things break:

1. **State doesn't scale.** The in-process rate limiter (`TokenBucketRateLimiter._buckets`) is per-process. Adding a 2nd uvicorn worker means each user gets 2× the rate limit (each worker has its own bucket). The cache (`TTLCache`) has the same problem.

2. **No auth for multiple teams.** The drafter was built for one tenant (PacificFreight). The 12-person CS team + Sarah's ops + Daniel's IT = 3 user groups in 1 tenant. But PacificFreight's new e-commerce customer (the one that brought the volume) is a different tenant. **A single-tenant service can't ship to a second tenant.**

3. **The sandbox is a subprocess.** The data analyst's sandbox blocks 99% of LLM-emitted code; the 1% it lets through runs in a subprocess. At 50 questions/day (Phase 4 volume), that's fine. At 500/day, a single matplotlib CVE becomes a SEV-1.

4. **The VM is in Singapore.** If the Singapore region has an outage (1 × per quarter, on average, for AWS), Mei's 12-person team is dead in the water for 4 hours. The CFO needs 99.95% SLA, which requires multi-region DR.

---

## The Phase 5 lift

Phase 5 takes the Phase 4 system — which works for 1 tenant, 1 region, 1 worker, 1 sandbox — and turns it into a system that works for **12 tenants, 2 regions, 8 workers, gVisor** at **99.95% SLA** with the same eval set, the same runbook, the same cost ceiling.

### 1. Externalize the state (P1)

**Before (Phase 4):** `TokenBucketRateLimiter._buckets` is a Python dict; `TTLCache` is an LRU; sessions are in-process. Adding a 2nd worker splits the rate limit and the cache.

**After (Phase 5, P1):** A `RedisTokenBucket` shares the bucket across all workers via a Lua script (atomic `INCR + EXPIRE`). A `RedisTTLCache` does the same for the LLM cache. A `RedisSessionStore` holds the per-tenant session tokens. The Phase 4 modules (`circuit.py`) keep their interface; the implementation flips to Redis. **13/13 Phase 3 tests still pass because the contract is unchanged.**

### 2. OAuth + multi-tenant (P2)

**Before (Phase 4):** The drafter has no auth. Anyone with the URL can call it. Mei's terminal has the URL; nobody else does. Fine for 1 team; not fine for 12.

**After (Phase 5, P2):** A `OAuthProvider` issues JWTs (RS256-signed) with a `tenant_id` claim. A `TenantResolver` middleware inspects every request, extracts the tenant, and applies the right policy file (now per-tenant YAML). Mei's `cs_junior` token at PacificFreight can't call refund.create at the e-commerce customer's tenant, even if she has a PacificFreight token.

### 3. gVisor sandbox (P3)

**Before (Phase 4):** The data analyst's sandbox is a subprocess + rlimit. The threat model is "the LLM emits code." Fine for that threat.

**After (Phase 5, P3):** The sandbox is a gVisor (`runsc`) container with no host filesystem, no network, no capabilities, no `/proc`, no `/sys`. The threat model is now "an untrusted user uploading code" (because the data analyst is now multi-tenant). gVisor costs 50ms per execution but handles 95% of CVEs that subprocess + rlimit doesn't.

### 4. Multi-region DR (P4)

**Before (Phase 4):** 1 VM in 1 region. The platform's health check fails; Caddy returns 503 for 4 hours.

**After (Phase 5, P4):** Active/passive DR with a read-replica in a 2nd region. Caddy's DNS is updated by a health check every 30s; failover is automatic; RPO < 30s, RTO < 30s. The 99.95% SLA is met.

---

## What the FDE delivers at the end of Phase 5

```
phase-5-advanced/
├── scenario-brief.md                     ← this file
├── projects/
│   ├── 01-redis-state/                   ← P1: Redis rate limit + cache + session
│   ├── 02-oauth-multi-tenant/            ← P2: JWT + per-tenant policy
│   ├── 03-gvisor-sandbox/                ← P3: gVisor replacement
│   └── 04-multi-region-dr/               ← P4: active/passive DR
├── technical/                            ← the 3 lessons
└── case-studies/                         ← the 5 scale-event postmortems
```

**35/35 tests pass** (13 Phase 3 + 4 MCP + 3 multi-agent + 2 SLM + 3 sandbox + 4 Redis + 3 OAuth + 2 gVisor + 1 multi-region).

---

## What's after Phase 5

There is no Phase 6 in this course. Phase 6 in a real company is K8s + service mesh + custom base models + SOC 2 + HIPAA + multi-cloud + on-prem deployment + 50+ engineers. That's a different course.

The Phase 5 portfolio is the principal-level FDE portfolio. **A principal FDE who has shipped all 5 phases can run any AI engagement, at any scale, in any region, with any threat model.** That's the job.

---

## Closing

The pattern didn't change: **eval-set-as-spec, runbook-as-contract, cost-ceiling-as-score, handoff-as-proof, state-externalization-as-precondition.** The scale did. The FDE's job is to ship the lift in a way that the eval set, the runbook, the cost ceiling, and the 5-question test **all keep passing**. That's what Phase 5 tests.

**Last updated:** 2026-10-09
