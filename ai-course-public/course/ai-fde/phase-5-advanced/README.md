# Phase 5 — Advanced (Scale, Multi-Tenancy, Multi-Region)

> **The customer is the same. The system goes from SMB-scale to enterprise-scale.** Redis replaces in-process state. OAuth replaces API keys. gVisor replaces subprocesses. Multi-region replaces single-region.

## What's here

```
phase-5-advanced/
├── README.md                    ← you are here
├── scenario-brief.md            ← The Phase 4→5 lift narrative
├── projects/                    ← 4 production-scale projects
│   ├── 01-redis-state/          ← rate limiter + session store go to Redis
│   ├── 02-oauth-multi-tenant/   ← JWT auth + per-tenant isolation
│   ├── 03-gvisor-sandbox/       ← gVisor replacement for subprocess sandbox
│   └── 04-multi-region-dr/      ← active/passive DR + read replica
├── technical/                   ← 3 lessons (.md each) on the why
│   ├── 01-state-externalization.md
│   ├── 02-auth-and-tenancy.md
│   └── 03-sandbox-hardening.md
└── case-studies/                ← 5 PE-grade case studies of scale-out events
    ├── engagement-6-multi-tenant-onboarding.md
    ├── engagement-7-region-failover.md
    ├── engagement-8-cost-ceiling-breach.md
    ├── engagement-9-evals-at-scale.md
    └── engagement-10-principal-handoff.md
```

## Why Phase 5 exists

The Phase 4 portfolio proves the FDE pattern works at **SMB scale** (12-150 drafts/day, 1-12 seats). Phase 5 proves it works at **enterprise scale**: 100k+ users, multi-region, multi-tenant, with cost ceilings that survive 10× growth without renegotiating the LLM contract. The 4 projects each attack a different bottleneck:

| Phase 4 limit | Phase 5 fix | Why it matters |
|---|---|---|
| In-process rate limiter dies at 1 process | **Redis token bucket** (Project 1) | 3+ uvicorn workers can share a rate limit |
| API-key auth, single tenant | **OAuth + JWT + tenant key** (Project 2) | 5 customer teams share 1 service |
| subprocess sandbox lets LLM escape | **gVisor sandbox** (Project 3) | Untrusted-code threat model |
| 1 VM in 1 region | **Active/passive DR + read replica** (Project 4) | 99.95% SLA, 30-second RTO |

## What you produce

- **35/35 tests pass** (25 Phase 4 + 4 Redis + 3 OAuth + 2 gVisor + 1 multi-region).
- The 5 case studies (engagements 6-10) are PE-grade postmortems of scale events.
- The 3 lessons are 1 page each, modeled on the Phase 4 lesson format.

## The pattern (Phase 5 addition)

Phase 1-4 taught: **eval-set-as-spec, runbook-as-contract, cost-ceiling-as-score, handoff-as-proof.** Phase 5 adds: **state-externalization-as-precondition**. A service that holds state in-process can't horizontally scale; a service that holds state in Redis can. The 4 projects each externalize a different piece of state:

| State | Phase 4 location | Phase 5 location | Project |
|---|---|---|---|
| Per-user rate-limit bucket | `TokenBucketRateLimiter._buckets` (dict) | Redis Lua script | 1 |
| Per-tenant session token | (none) | Redis hash | 2 |
| Sandbox execution state | subprocess tmpdir | gVisor container | 3 |
| Multi-region DR state | (none) | Redis Sentinel + S3 | 4 |

## The 5-question Phase 5 test (additions)

Phase 5 expands the "FDE has left" test with 2 new questions:

6. Can a new uvicorn worker join the cluster without state loss? (Phase 5 P1)
7. Can a new tenant be onboarded in < 1 hour by editing 1 config file? (Phase 5 P2)
8. Can the sandbox survive a CVE in `matplotlib`? (Phase 5 P3)
9. Can a region failover happen in < 30 seconds with no data loss? (Phase 5 P4)
10. Can a new FDE answer all 9 of the above + the original 5 by day 30? (principal-level)

## How to use this phase

1. **Read `scenario-brief.md`** for the Phase 4→5 narrative (PacificFreight grows from 12 to 120 people; the drafter goes from 150 to 15,000 drafts/day).
2. **Pick a project, do it end-to-end.** Each project is self-contained; you can take a break between them.
3. **Run the tests.** Phase 5 adds 10 tests (35/35 total). The pytest count is the bar.
4. **Write the case studies.** Each project ships with 1 case-study template; the engagement narrative (engagement 6-10) is the artifact that survives the FDE's exit.

## File layout

```
phase-5-advanced/
├── README.md                              ← you are here
├── scenario-brief.md                      ← the Phase 4→5 lift
├── projects/
│   ├── 01-redis-state/
│   │   ├── service/redis_state.py        ← Redis-backed rate limiter + session
│   │   ├── service/redis_client.py       ← thin wrapper around redis-py
│   │   └── tests/test_redis_state.py     ← 4 tests (Lua atomicity, TTL, failover)
│   ├── 02-oauth-multi-tenant/
│   │   ├── service/oauth.py              ← JWT issue + verify
│   │   ├── service/tenant.py             ← tenant resolver (header → config)
│   │   └── tests/test_oauth.py           ← 3 tests (issue, verify, tenant isolation)
│   ├── 03-gvisor-sandbox/
│   │   ├── service/gvisor_runner.py      ← gVisor `runsc` wrapper
│   │   └── tests/test_gvisor.py          ← 2 tests (escape, no-network)
│   └── 04-multi-region-dr/
│       ├── service/health.py             ← active/passive + sentinel pings
│       └── tests/test_multi_region.py    ← 1 integration test (failover timing)
├── technical/                             ← 3 lessons
│   ├── 01-state-externalization.md
│   ├── 02-auth-and-tenancy.md
│   └── 03-sandbox-hardening.md
└── case-studies/                          ← 5 scale-event postmortems
    ├── engagement-6-multi-tenant-onboarding.md
    ├── engagement-7-region-failover.md
    ├── engagement-8-cost-ceiling-breach.md
    ├── engagement-9-evals-at-scale.md
    └── engagement-10-principal-handoff.md
```

## What's NOT in Phase 5

- **K8s / service mesh / Istio.** Phase 5 uses systemd + uvicorn workers + Caddy. K8s is a Phase 6 topic.
- **Microservices.** The Phase 4 service is a monolith; Phase 5 keeps it that way. Phase 6 splits when 30+ engineers are involved.
- **Custom model serving.** The SLM uses ollama/vLLM with off-the-shelf Qwen. Fine-tuning your own base model is a Phase 6 topic.
- **Compliance (SOC 2, HIPAA, PCI).** Phase 5 ships a redactor; a compliance-grade redactor is a Phase 6 topic.

## The thesis

A principal FDE's job is to make themselves unnecessary. Phase 5 tests that the FDE's pattern survives scale, multi-tenancy, sandbox hardening, and multi-region DR. The 4 projects are the lift; the 5 case studies are the proof; the 3 lessons are the why.

**Eval-set-as-spec. Runbook-as-contract. Cost-ceiling-as-score. Handoff-as-proof. State-externalization-as-precondition.**

---

**Last updated:** 2026-10-09
**Length:** ~6 weeks full-time (assuming Phase 1-4 complete)
**Cost:** $0 mock-mode + ~$50/mo for the Redis + read-replica infra in production
**Goal:** You can put "AI FDE @ enterprise scale" on your LinkedIn.
