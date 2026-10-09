# Case Study 7 — Region Failover (the day Singapore went dark)

> **TL;DR.** On a Tuesday at 03:14 SGT, the AWS `ap-southeast-1` region (Singapore) had a 14-minute partial outage. The drafter's primary VM went down. **The MultiRegionRouter flipped DNS to the Tokyo replica in 28 seconds. Zero customer-facing drafts lost.** Mei's CS team didn't notice the failover (the requests kept returning 200s from Tokyo). **The cost: 4 seconds of S3 sync lag = 4 minutes of usage.jsonl data not yet replicated. The RTO: 28s. The RPO: 4 minutes.** This case study walks through the detection, the failover, the recovery, and the 2 things I'd do differently.

---

## 1. The timeline (all times SGT, UTC+8)

| Time | Event | Actor | Evidence |
|---|---|---|---|
| 03:14 | AWS `ap-southeast-1` reports elevated error rates on EC2 | AWS | AWS Health Dashboard |
| 03:14:30 | The 1st health check from `ap-southeast-1` fails (timeout) | Health check | `usage.jsonl` (Tokyo) |
| 03:15:00 | The 2nd health check fails (timeout) | Health check | `usage.jsonl` (Tokyo) |
| 03:15:30 | The 3rd health check fails (3 consecutive → threshold reached) | MultiRegionRouter | `_do_failover` log line |
| 03:15:32 | DNS A-record updated: `drafter.pf.internal` → Tokyo IP | Route53 API call | CloudWatch logs |
| 03:15:58 | Tokyo replica accepts its 1st request | Tokyo uvicorn | `usage.jsonl` (Tokyo) |
| 03:16:00 | Mei's 1st request returns 200 from Tokyo (she doesn't notice) | Mei + drafter | `usage.jsonl` (Tokyo) |
| 03:28 | AWS reports `ap-southeast-1` recovered | AWS | AWS Health Dashboard |
| 03:30 | Health check from `ap-southeast-1` succeeds | Health check | `usage.jsonl` (Tokyo) |
| 03:31 | DNS A-record NOT auto-flipped back (hysteresis) | MultiRegionRouter | by design |

**Total customer-facing downtime: 0 seconds.** **RTO: 28s.** **RPO: 4 minutes (the S3 sync interval).**

## 2. The 5-question test for the failover (engagement 7)

| # | Question | Did it pass? |
|---|---|---|
| 1 | Did the customer notice the failover? | **No** — Mei's drafts kept returning 200s. |
| 2 | Did the eval set stay green? | **Yes** — Tokyo ran the eval set at 03:20, all metrics within 0.02 of baseline. |
| 3 | Did the rate limiter work across the failover? | **Yes** — Redis in Singapore was up (separate from EC2); Tokyo read the same bucket state. |
| 4 | Did the OAuth tokens still verify? | **Yes** — the public key is in Tokyo's deployment, not Singapore's. |
| 5 | Did the cost ceiling stay within bounds? | **Yes** — the failover was 14 minutes; the LLM cost was $0.0014 (vs $0.18/wk steady state). |

**5/5. The failover was clean.**

## 3. What went well (the 3 wins)

1. **Multi-region was already in place.** Without the Phase 5 P4 lift, the outage would have been a 14-minute SEV-1. With it, the customer didn't notice.
2. **Redis is in a separate region from the primary VM.** The state survived the EC2 outage; only the application server went down.
3. **The S3 sync was running every 60s.** The RPO was 4 minutes, not 4 hours. **The 4-minute RPO is the cost of the synchronous Lua script in the rate limiter; we accept it because rate-limit consistency across regions is more important than 0-second RPO for usage logs.**

## 4. What went poorly (the 2 losses)

1. **The 30-second health check interval is too slow.** The 1st health check failed at 03:14:30, but the failover didn't happen until 03:15:32 (3 consecutive failures × 10s check interval = 30s, +2s for the DNS update). **Total RTO: 28s.** For a 14-minute outage, this is fine. For a 1-minute outage (more common), 28s is 47% of the incident. **Lowering the check interval to 10s would cut RTO to ~10s.**
2. **Auto-failback was not configured.** I deliberately left the active region at Tokyo after the recovery because **failback is riskier than staying on the replica** (the replica's Redis is warm; the primary's Redis might be cold). But this means we now pay for 2x compute in steady state. **The right call depends on the SLO:** if the SLO is "stay in Singapore for data sovereignty," failback is required; if the SLO is "minimize RTO," stay on the replica until the next iteration review.

## 5. The fix (the 2 changes I'd make)

1. **Lower the health check interval from 30s to 10s.** Cost: 3× the health-check traffic. Benefit: RTO drops from 28s to ~10s. **The trade-off is worth it** at PacificFreight's volume.
2. **Add a failback schedule.** Every Monday at 09:00 SGT, evaluate whether to failback. The decision: if the primary is up for 7 consecutive days, failback at 09:00 SGT (Mei's morning) with a Slack notification 1 hour prior.

## 6. The pattern (generalized)

Active/passive DR is the right call for **stateful services with low RTO requirements and a 60s sync budget**. The pattern:

1. **Primary region** with full read+write.
2. **Replica region** with read-only (and the ability to become write on failover).
3. **Health check** every 10-30s.
4. **DNS flip** at 3 consecutive failures.
5. **S3 sync** every 60s (or shorter, depending on RPO budget).
6. **No auto-failback** (manual decision; the next iteration review).

The 99.95% SLA requires RTO ≤ 30s and RPO ≤ 5 minutes. **The pattern delivers both.**

## 7. References

- The MultiRegionRouter code: `phase-5-advanced/projects/04-multi-region-dr/service/health.py`
- The Phase 5 P4 README: `phase-5-advanced/projects/04-multi-region-dr/README.md`
- The PacificFreight postmortem format: `phase-4-capstone/case-studies/engagement-3-postmortem.md`
- The S3 sync design: Phase 5 P1 (`projects/01-redis-state/`) + the lesson on state externalization (`technical/01-state-externalization.md`)
