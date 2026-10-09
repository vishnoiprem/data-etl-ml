# Case Study 8 — The Cost Ceiling Breach (when 100× growth meets the bill)

> **TL;DR.** When PacificFreight grew 100× (150 → 15,000 drafts/day), the LLM bill went from $0.50/wk to $180/wk — **3.6× over the $5/month ceiling**. The breach was detected by the Prometheus alert at $4/wk → $50/mo → page on-call. **The fix took 3 weeks and combined all 4 Phase 5 projects: Redis (P1, to share rate limit across workers), OAuth + multi-tenant (P2, so the e-commerce customer pays for their own usage), gVisor (P3, not relevant to cost but part of the scale-up), and multi-region (P4, to spread the load).** The final bill at 10× growth settled at $4.09/mo, under the ceiling. **The lesson: cost ceilings are not ROI targets; they are constraints. The architecture that satisfies the constraint at 10× is the same architecture that satisfies it at 100×.**

---

## 1. The detection (Monday 09:00 SGT iteration review)

The Monday iteration review is when Sarah (ops) and Daniel (IT) check the cost dashboard. On this Monday, the alert had fired 3 times over the weekend: at $4/wk on Friday, at $5/wk on Saturday, at $8/wk on Sunday. The actual bill was $25 by Sunday night.

```
$ python3 /opt/pf-drafter/bin/cost_report.py
Weekly LLM bill: $180.00
Monthly projection (× 4.33): $779.40
Cost ceiling: $5.00 / month
Status: BREACH (155.88x over)
```

The 100× volume growth wasn't matched by a 100× budget growth because the budget was set when PacificFreight was a 12-person SMB. The customer was now 120 people, but the budget was still $5/mo.

## 2. The 3-week fix (what shipped)

### Week 1: emergency throttle

- **Tightened the rate limit** from 60/min/user to 20/min/user. The drafter still works, but Mei's team can't accidentally loop it.
- **Disabled the SLM test** (the Qwen 1.5B was serving 80% of traffic; turning it off forces all traffic to GPT-4o-mini at $0.15/1M, which is more expensive per draft but lets us audit quality).
- **Result:** bill dropped from $180/wk to $90/wk. Still 36x over.

### Week 2: multi-tenant split

- **Migrated the e-commerce customer (ECommercePlatform) to a separate tenant** with their own budget ($50/mo). The e-commerce customer's volume was 80% of the overage.
- **The PacificFreight tenant's bill dropped to $25/wk.** Still 5x over their $5/mo ceiling.
- **Result:** $25/wk PF + $90/wk ecom = $115/wk total. The ecom customer is paying for their own usage.

### Week 3: SLM at 90% routing

- **Brought the SLM back online** for the routine regime (80% of traffic).
- **Result:** PF tenant: $5/wk. ecom tenant: $25/wk. Total: $30/wk = $130/mo. The ecom ceiling is $50/mo; still over.
- **Tightened the ecom rate limit** to 100/min/user. Final: $4.09/mo at 10× growth, under the ecom $50/mo ceiling.

## 3. The 5-question test (engagement 8)

| # | Question | Did it pass? |
|---|---|---|
| 1 | Did the cost ceiling protect the customer? | **Yes** — without the alert at $4/wk, the bill would have reached $1,000+ before anyone noticed. |
| 2 | Did the multi-tenant split work? | **Yes** — PacificFreight's bill is now $5/wk (down from $25); the e-commerce customer pays their own. |
| 3 | Did the SLM still produce 79%+ thumbs-up? | **Yes** — Mei's quality didn't drop; the SLM was the right call. |
| 4 | Did the 5-question test still pass? | **Yes** — all 3 stakeholders answered 5/5 at the 30-day check. |
| 5 | Did the customer sign off on the multi-tenant split? | **Yes** — Sara (ECommercePlatform) approved the new YAML within 1 hour of the proposal. |

**5/5. The fix worked.**

## 4. The 5 changes I'd make

1. **Set the cost ceiling at 50% of the customer's willingness-to-pay, not 100%.** Mei's willingness-to-pay at 100× growth is $50/mo, not $5/mo. The ceiling should have been $25/mo, which would have given 5 weeks of warning instead of 1.
2. **Auto-scale the SLM routing share.** At 80% SLM + 20% GPT, the bill is $30/wk. At 90% SLM + 10% GPT, the bill is $20/wk. The router should adapt based on the bill trajectory, not the user-facing metric.
3. **Pre-approve the multi-tenant YAML for the 2nd tenant.** The 4-hour onboarding is great; it would be even better if the YAML were pre-approved when the 2nd tenant signs the contract. Saves 2 hours of legal review.
4. **Add a "growth event" detector.** When Mei's team goes from 12 to 120, the cost trajectory changes by an order of magnitude. **The system should detect the growth and proactively propose the multi-tenant split, not wait for the cost ceiling to breach.**
5. **Make the cost ceiling a config, not a code change.** The ceiling is in `app.py` (the `cost_per_min_usd_threshold=5.0`). It should be in a per-tenant YAML, alongside the model choice and the rate limit.

## 5. The pattern (generalized)

The cost ceiling is **the spec, not the savings target.** When the volume grows by 100×, the architecture has to change:

- **Single tenant → multi-tenant** (P2): each tenant pays for their own usage.
- **In-process state → Redis** (P1): horizontal scale requires shared state.
- **GPT-4o-mini only → 80/20 SLM routing** (Phase 4 P3 + Phase 5 tuning): cost reduction without quality loss.
- **Single region → multi-region** (P4): scale-out without downtime.

**The eval set is the spec; the cost ceiling is the test; the architecture is the answer.** When the cost ceiling is breached, the architecture is wrong, not the ceiling.

## 6. References

- The Phase 4 SLM cost model: `phase-4-capstone/case-studies/engagement-4-slm-cost.md`
- The Phase 5 multi-tenant onboarding: `phase-5-advanced/case-studies/engagement-6-multi-tenant-onboarding.md`
- The cost ceiling alert: `phase-2-core-build/service/circuit.py::CircuitBreakerConfig.cost_per_min_usd_threshold`
- The 5-question test: `phase-4-capstone/case-studies/engagement-5-handoff.md`
