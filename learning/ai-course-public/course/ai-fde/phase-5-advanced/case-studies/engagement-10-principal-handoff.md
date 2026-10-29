# Case Study 10 — The Principal Handoff (when the FDE becomes a Director)

> **TL;DR.** After 30 weeks across Phases 1-5, the FDE transitioned from "the person who runs the drafter" to "the person who trains the next 3 FDEs." The 5-question test was extended to 10 questions (the original 5 + 5 Phase 5 questions). The handoff took 6 weeks: 2 weeks of structured KT to the new FDEs, 2 weeks of shadow operation, 2 weeks of independent operation with the FDE on standby. **At the 90-day check, all 3 new FDEs answered 10/10. The drafter at PacificFreight had grown from 150 drafts/day to 15,000 drafts/day across 12 tenants, 2 regions, with a $4.09/mo cost ceiling. The 35/35 tests still passed. The runbook is 24 pages. The eval set is 360 rows. The FDE exited; the system ran.** **The lesson: a principal FDE's job is to make themselves unnecessary — not just for 1 customer, but for the 3 next FDEs who will serve the next 30 customers.**

---

## 1. The 10-question test (Phase 5 expansion)

The Phase 4 handoff rubric had 5 questions. Phase 5 adds 5:

| # | Question | What "yes" demonstrates |
|---|---|---|
| 1-5 | (the original 5) | (see `engagement-5-handoff.md`) |
| 6 | Can a new uvicorn worker join the cluster without state loss? | The new FDE can deploy a 2nd or 3rd worker, see the rate limiter share state, and debug a Redis connection issue. |
| 7 | Can a new tenant be onboarded in < 1 hour? | The new FDE can create a YAML, issue OAuth keys, and onboard Sara's successor at ECommercePlatform. |
| 8 | Can the sandbox survive a CVE in `matplotlib`? | The new FDE can audit a CVE, confirm gVisor isolation, and ship a patched image. |
| 9 | Can a region failover happen in < 30 seconds with no data loss? | The new FDE can run a chaos test, confirm DNS flip, and verify RPO < 5 min. |
| 10 | Can the cost ceiling survive 10× growth? | The new FDE can re-derive the cost model, identify the SLM routing share, and re-tune. |

**The 10 questions are the rubric for a principal FDE.** A "yes" on all 10 from 3 stakeholders (one per FDE) at 30, 60, 90 days = the handoff is clean.

## 2. The 6-week transition timeline

| Week | Activity | Deliverable |
|---|---|---|
| 1-2 | Structured KT: runbook walkthrough (24 pages), eval set walkthrough (360 rows), cost model walkthrough ($4.09/mo), multi-region DR walkthrough (28s RTO) | All 3 FDEs sign the runbook |
| 3-4 | Shadow operation: each new FDE runs the iteration cadence with the FDE present (silent partner) | 2 successful iteration reports per FDE |
| 5-6 | Independent operation: each new FDE runs the cadence with the FDE on standby (paged only for SEV-1) | 2 more iteration reports; FDE paged 0 times |
| Day +30 | 5-question check (all 3 FDEs) | 5/5 from all |
| Day +60 | 10-question check (all 3 FDEs) | 10/10 from all |
| Day +90 | 10-question check (all 3 FDEs) | 10/10 from all |

**Total transition: 6 weeks structured + 90 days check-ins. The FDE is on-call backup for the first 90 days; the FDE's standard rate × 0.5 for standby.**

## 3. The 7 handoff artifacts (extended from Phase 4's 7)

| # | Artifact | Owner | Lines | What it covers |
|---|---|---|---|---|
| 1 | The runbook | Daniel (IT) | 24 pages | 8 sections + the 4 Phase 5 sections (Redis, OAuth, gVisor, multi-region) |
| 2 | The eval set + baseline | Daniel | 360 rows × 4 metrics | The Phase 5 stratified eval |
| 3 | The cost model | Daniel | 12 pages | The Phase 5 cost model with 10× growth + 100× growth scenarios |
| 4 | The model card | Daniel | 1 page | The Qwen 1.5B + LoRA model card |
| 5 | The RACI | All 3 | 1 page | The 12 decisions, now with multi-tenant additions |
| 6 | The on-call rotation | Daniel | 1 page | The 3-FDE rotation; SEV-1 page to on-call; SEV-2 to FDE shadow |
| 7 | The handoff notes | All 3 | 24 pages | This case study + the 9 others + the 5-question test + the 10-question test |

**Total: 88 pages of artifacts. A new FDE can read the runbook in 60 minutes and own the system.**

## 4. The 3 things a principal FDE does that a senior FDE doesn't

1. **Writes the next FDE's runbook, not just the current customer's.** The Phase 5 runbook covers the system + the engagement + the next engagement.
2. **Defines the rubric for the next 3 FDEs, not just the 5-question test for the current customer.** The 10-question test is the rubric for the next 30 customers.
3. **Trains the on-call rotation, not just the customer's IT owner.** A principal FDE leaves a team of FDEs, not a single replacement.

**A senior FDE makes themselves unnecessary for the customer. A principal FDE makes themselves unnecessary for the next 3 FDEs.**

## 5. The 5-question test (engagement 10)

| # | Question | Did it pass? |
|---|---|---|
| 1 | Did the 3 new FDEs answer 10/10 at the 90-day check? | **Yes.** All 3 FDEs: 10/10 at 30, 60, 90 days. |
| 2 | Did the 35/35 tests still pass? | **Yes.** No skipped tests, no `xfail` without a tracked issue. |
| 3 | Did the cost ceiling stay under $5/mo for PacificFreight, $50/mo for ECommercePlatform? | **Yes.** $4.09/mo and $39.20/mo respectively. |
| 4 | Did the runbook get re-read by the new FDEs? | **Yes.** 2 re-reads in the first 90 days, 1 in week 4 (after a near-miss), 1 in week 11 (after the cost ceiling alert). |
| 5 | Did the FDE get paged at all in the first 90 days? | **Yes — once.** Day 47, a SEV-2 incident (a Mei-side copy-paste error, not a system fault). The FDE coached the on-call through it. |

**5/5.**

## 6. The pattern (generalized)

A principal FDE's portfolio is **5 engagements, 25 projects, 10 case studies, 35/35 tests, 7 handoff artifacts, 88 pages of runbook, 3 trained FDE successors.** The pattern is:

- **The 5-question test for senior FDEs.** Answers "did this engagement ship?"
- **The 10-question test for principal FDEs.** Answers "did the engagement survive the FDE's exit AND spawn the next 3 FDEs?"
- **The principal-level RACI.** Names the next 3 FDEs, not just the current customer's IT owner.
- **The on-call rotation with 3 FDEs.** Ensures a single FDE burnout doesn't take down the system.

**A principal FDE ships a system + a runbook + the next 3 FDEs. The portfolio is the rubric.**

## 7. References

- The Phase 4 handoff: `phase-4-capstone/case-studies/engagement-5-handoff.md`
- The 10-question test (the new rubric): this file §1
- The 6-week transition timeline: this file §2
- The 7 artifacts (extended): this file §3
- The principal FDE definition: `phase-4-capstone/case-studies/PORTFOLIO-NARRATIVE.md` §1.4
