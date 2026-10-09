# Case Study 5 — The Handoff (when the FDE leaves)

> **TL;DR.** After 12 weeks, I handed the PacificFreight drafter to Daniel. The handoff took 2 weeks of structured transition (knowledge transfer + ownership ceremonies + regression-detection setup), plus a 60-day post-handoff check-in cadence. The 5-question "FDE has left" test — answered independently by Daniel, Mei, and Sarah at 30, 60, and 90 days — confirmed the handoff was clean. **At the 90-day check, all 3 stakeholders answered all 5 questions correctly; the iteration cadence ran every Monday; 2 SEV-1 candidates occurred (both caught + rolled back in < 60 min); the bill stayed at $0.48/wk; thumbs-up stayed at 82%.** **The lesson:** the handoff is the engagement. Everything before the handoff is preparation. The handoff is mechanical (5 artifacts × 3 stakeholders × 3 check-ins), not heroic. **A principal FDE's job is to make themselves unnecessary.**

---

## 1. The 5-question "FDE has left" test (the rubric)

The 5 questions are asked of every stakeholder independently, 30+ days after the FDE's last commit. A "yes" on all 5 from all stakeholders = the handoff is clean.

| # | Question | What a "yes" answer demonstrates |
|---|---|---|
| 1 | What does the drafter do? | The stakeholder can describe the system in 1 sentence without the FDE's help. |
| 2 | How do you know it's working? | The stakeholder knows the observable metric for their role. |
| 3 | What breaks first when it goes wrong? | The stakeholder can name the most-likely failure mode for their role. |
| 4 | How do you fix it? | The stakeholder can either fix it themselves or name the person who can. |
| 5 | What's the cost ceiling, and how do you know when you've hit it? | The stakeholder knows the budget and the alert. |

### 1.1 Daniel's answers (the IT owner) — 30-day check

1. "Drafts replies to customer emails using RAG over our policy corpus and shipment data."
2. "The eval set runs every Monday at 09:00 SGT. Faithfulness stays above 0.85; thumbs-up stays above 70%."
3. "The retriever returns 0 chunks for a query (the corpus is empty for that shipment ID). Mei gets a generic draft and reverts it."
4. "Open the runbook, section 'retriever returns empty'. The fix is `docker restart rag` and `python3 admin/reindex.py`."
5. "$5/month. The Prometheus alert fires when the weekly bill exceeds $4."

### 1.2 Mei's answers (the CS user) — 30-day check

1. "Drafts replies to customer emails so I don't have to write them from scratch."
2. "My thumbs-up rate. If it drops below 70%, something's wrong."
3. "The draft mentions the wrong shipment status (e.g., says delivered when it's held at customs). I revert and re-read the corpus."
4. "I tell Daniel. He re-runs the eval set and re-deploys if needed."
5. "I don't know — Daniel tracks the bill."

### 1.3 Sarah's answers (the ops user) — 30-day check

1. "I don't use the drafter directly. I use the multi-agent dispatcher's summary for multi-shipment cases."
2. "The aggregate stats at the top of the daily ops review. If they drop, something's wrong."
3. "The dispatcher trace shows that an agent ran but produced empty output. I re-run the case."
4. "I tell Daniel. He checks the agent's circuit breaker."
5. "I don't know — Daniel tracks the bill."

### 1.4 What these answers reveal

| Stakeholder | Knows what they need | Defers appropriately | Verdict |
|---|---|---|---|
| Daniel (IT) | All 5 questions | N/A — owns all of it | ✅ Full owner |
| Mei (CS) | Q1-Q4 (her lane) | Q5 (cost is Daniel's lane) | ✅ Lane-aware |
| Sarah (Ops) | Q1-Q4 (her lane) | Q5 (cost is Daniel's lane) | ✅ Lane-aware |

**The handoff is clean when each stakeholder knows their lane and defers the rest to the right owner.** Mei doesn't need to know the cost ceiling; Daniel does. Sarah doesn't need to know the thumbs-up rate; Mei does. **Lane awareness is the test; full-stack knowledge is not the goal.**

### 1.5 The 30/60/90-day results

| Check | Daniel (5/5) | Mei (4/5) | Sarah (4/5) | Iter cadence | Bill | Thumbs-up | SEV-1 |
|---|---|---|---|---|---|---|---|
| **30 days** | ✅ | ✅ (Q5 deferred) | ✅ (Q5 deferred) | Every Mon | $0.48/wk | 82% | 0 |
| **60 days** | ✅ | ✅ | ✅ | Every Mon | $0.55/wk | 81% | 1 (the case study #3 incident, 38-min MTTR) |
| **90 days** | ✅ | ✅ | ✅ | Every Mon | $0.49/wk | 82% | 1 (similar to W11, caught in < 30 min by the now-mature eval-CI gate) |

---

## 2. The handoff artifacts (the 7 things that survived the FDE's exit)

The handoff shipped 7 artifacts. Each is a "no, the FDE didn't take this with them" deliverable — these are the things the customer's team uses after the FDE is gone.

| # | Artifact | Location | Owner (post-handoff) | Why this matters |
|---|---|---|---|---|
| 1 | **The runbook** | `phase-3-deployment/consulting/runbook.md` | Daniel | The contract. 8 sections, 12 pages. |
| 2 | **The eval set + baseline** | `shared/eval_set.jsonl` + `shared/baseline.jsonl` | Daniel | The regression detector. 30 rows + 4 metrics + threshold. |
| 3 | **The cost model** | `shared/cost_model.md` | Daniel | The ceiling + the alert. |
| 4 | **The model card** | `projects/03-distilled-slm/slm/model_card.md` | Daniel | The SLM's contract. 77% quality ratio with full derivation. |
| 5 | **The RACI** | `phase-3-deployment/consulting/raci.md` | Daniel | Who decides what. |
| 6 | **The on-call rotation** | `phase-3-deployment/consulting/on-call-rotation.md` | Daniel | Whose phone rings at 2am. |
| 7 | **The handoff notes** | `course/ai-fde/phase-4-capstone/case-studies/engagement-5-handoff.md` (this file) | All 3 | The proof. The 5-question test. |

### 2.1 The runbook (artifact #1) — section map

| Section | Pages | Purpose | Owner |
|---|---|---|---|
| 1. Overview (system diagram, endpoints, 13/13 tests) | 2 | "What is this thing?" | Daniel |
| 2. Daily ops (eval set, iteration cadence, rollback) | 2 | "What do I do on a Monday?" | Daniel |
| 3. Weekly ops (cost review, corpus review, SLM retrain) | 2 | "What do I do once a week?" | Daniel |
| 4. Incident response (SEV-1 playbook, 3-tier fallback, postmortem template) | 3 | "What do I do at 2am?" | Daniel (page FDE for SEV-1) |
| 5. On-call rotation (who's on call, escalation tiers, contact info) | 1 | "Whose phone rings?" | Daniel |
| 6. RACI | 1 | "Who decides what?" | All 3 |
| 7. Glossary (acronyms, tools, metrics) | 1 | "What does RAGAS stand for?" | All 3 |
| 8. 5-question test | 1 | "Did the handoff work?" | All 3 |

**Total: 12 pages, 8 sections.** A new FDE can read this in 30 minutes and know the system. **A new IT owner (Daniel's replacement) can read this in 60 minutes and own the system.**

---

## 3. The handoff timeline (2 weeks of structured transition)

The handoff is not a single meeting. It's 2 weeks of ceremonies, each with a specific deliverable. The 2 weeks start in week 11 of the engagement (the customer is in steady state) and end in week 12 (the FDE exits).

### 3.1 Week 11 — Knowledge transfer (Daniel is the primary)

| Day | Ceremony | Duration | Deliverable | Attendees |
|---|---|---|---|---|
| Mon | Runbook walkthrough (live) | 2 hr | Daniel signs the runbook | FDE, Daniel, Mei |
| Tue | Eval set + iteration cadence walkthrough (live) | 1 hr | Daniel runs the eval set himself | FDE, Daniel |
| Tue | Eval set regression: FDE introduces a deliberate regression; Daniel catches it | 1 hr | Daniel's first rollback | FDE, Daniel |
| Wed | Cost model + Prometheus alerts walkthrough | 1 hr | Daniel shows the dashboard | FDE, Daniel |
| Wed | On-call rotation: FDE triggers a SEV-2 alert (deliberately), Daniel pages himself | 30 min | Daniel's first on-call | FDE, Daniel |
| Thu | SLM re-train (live) | 2 hr | Daniel saves the new adapter | FDE, Daniel |
| Thu | Multi-agent orchestrator walkthrough | 1 hr | Daniel runs the orchestrator | FDE, Daniel, Sarah |
| Fri | RACI review (live) | 1 hr | All 3 sign the RACI | FDE, Daniel, Mei, Sarah |
| Fri | 5-question test (live, all 3 stakeholders, FDE present) | 30 min | All 5/5; if not, fix the gap | FDE, Daniel, Mei, Sarah |

**Total week 11: ~10 hours of structured KT.**

### 3.2 Week 12 — Independent operation + FDE exit

| Day | Ceremony | Duration | Deliverable | Attendees |
|---|---|---|---|---|
| Mon | Iteration cadence (Daniel runs solo) | 1 hr | Iteration report signed by Daniel | Daniel, Mei |
| Tue | FDE silent on Slack | 24 hr | Customer solves their own problem | All |
| Wed | FDE silent on Slack (continued) | 24 hr | Customer solves their own problem | All |
| Thu | FDE silent on Slack (continued) | 24 hr | Customer solves their own problem | All |
| Fri | 5-question test (live, all 3, FDE silent) | 30 min | All 5/5 again; if not, fix the gap | Daniel, Mei, Sarah |
| Fri | FDE commits last PR; closes the laptop | 0 hr | Last commit: `docs(handoff): sign-off` | FDE |
| Fri | 60-day check-in calendar invite sent | 0 hr | Outlook invite for 60-day check | All 3 + FDE |

**Total week 12: ~5 hours of customer-led operations, 0 hours of FDE heroics.**

### 3.3 The "FDE silent on Slack" rule

During days Tue-Thu of week 12, the FDE does not respond to Slack messages. **This is the most important ceremony.** It is the test that the customer can operate without the FDE. If the customer escalates a question that only the FDE can answer, that's a KT gap that the FDE fixes (in week 13, which the FDE bills for at 1.5× the standard rate to discourage this from happening).

**In the PacificFreight engagement, the customer did not need the FDE in days Tue-Thu of week 12.** They had 2 questions, both answered by Daniel from the runbook. The 5-question test on Friday was 5/5 from all 3 stakeholders. **The handoff was clean.**

---

## 4. The 3 failure modes I'm most worried about (the things that will fail after I leave)

A principal FDE writes a "what's likely to break first" section. These are the 3 things the FDE is most worried about, ranked by probability × blast radius.

### 4.1 Failure mode 1 — The policy corpus goes stale

| Field | Value |
|---|---|
| **Failure** | Daniel doesn't update the policy corpus when Singapore customs rules change (this happens ~2× per year) |
| **Detection lag** | 2-4 weeks (the next customer escalation about a wrong answer) |
| **Blast radius** | All drafts that touch the changed policy area |
| **Mitigation** | Daniel owns the corpus; the iteration report flags "policy corpus age > 30 days" as a warning |
| **Recovery time** | 15 min (Daniel re-indexes) |

### 4.2 Failure mode 2 — The SLM's training data goes stale

| Field | Value |
|---|---|
| **Failure** | Mei's writing style evolves; the SLM trained on last week's drafts is suboptimal |
| **Detection lag** | 1-2 weeks (thumbs-up rate drift, caught by Monday cadence) |
| **Blast radius** | 80% of drafts (the routine regime) |
| **Mitigation** | SLM re-trains weekly (every Monday after the iteration cadence); the eval set detects drift |
| **Recovery time** | 30 min (re-train + redeploy) |

### 4.3 Failure mode 3 — The cost ceiling is hit (10× growth)

| Field | Value |
|---|---|
| **Failure** | 5 customer teams start using the drafter; the bill spikes above $5/month |
| **Detection lag** | 1-3 days (the Prometheus alert) |
| **Blast radius** | All users (cost over-runs) |
| **Mitigation** | Prometheus alert at $4/wk; Daniel investigates; SLM increases its routing share from 80% to 90% |
| **Recovery time** | 1 hr (config change) |

### 4.4 The 60-day check-in (the proof)

The FDE checks in at 30, 60, and 90 days. Each check-in is a 30-minute call with Daniel + Mei + Sarah, structured as:

| Section | Time | Question |
|---|---|---|
| Quantitative metrics | 10 min | What were the numbers? (thumbs-up, bill, eval, uptime) |
| Incidents | 10 min | What broke? How long to recover? |
| 5-question test | 5 min | Repeat the 5 questions, all 3 stakeholders |
| What's hard? | 5 min | What did you need the FDE for that you didn't have? |

**At the 60-day check:** 0 SEV-1 incidents (one was caught at the 11-week mark — that's Case Study #3), 2 SEV-3 incidents (cron failures caught by the new alerts, no user impact), 1 question that the FDE answered (the SLM re-train config — a 5-min fix). The 5-question test was 5/5 from Daniel, 4/5 from Mei (she had forgotten the cost ceiling's exact number — a 30-second refresher), 4/5 from Sarah (same as Mei).

**The 5-minute fix is the proof that the handoff is real.** Mei's Q5 lapse was 30 seconds of "the ceiling is $5/month, the alert is at $4/wk, the runbook is in section 3.3." This is not a knowledge gap; it's a recall gap. Recall is solved by re-reading the runbook, not by re-doing the KT.

---

## 5. The ownership transition (the RACI)

The RACI is the artifact that names the new owners. It's the difference between "the FDE owned this" and "Daniel owns this now." Without the RACI, the handoff is a vibe; with the RACI, the handoff is a contract.

### 5.1 The 12 decisions in the engagement

| Decision | R (Responsible) | A (Accountable) | C (Consulted) | I (Informed) | Notes |
|---|---|---|---|---|---|
| Eval set composition | Daniel | Daniel | Mei | Sarah | 30 rows, 4 categories, 3 difficulties |
| Prompt changes | FDE (during engagement) → Daniel (post-handoff) | Daniel | Mei | Sarah | Must pass eval set in CI |
| LLM model choice | Daniel | Daniel | FDE (advisory) | Mei | gpt-4o-mini vs alternatives |
| Cost ceiling | Daniel | CEO (PacificFreight) | Mei, Sarah | FDE | $5/month, alert at $4/wk |
| Deploy window | Daniel | Daniel | Mei | Sarah | 14:00-16:00 SGT block |
| Incident response (SEV-1) | Daniel | Daniel | FDE (on-call backup) | Mei, Sarah, CEO | 60-min MTTR SLO |
| Incident response (SEV-2) | Daniel | Daniel | Mei (if CS-related) | Sarah | 4-hr MTTR SLO |
| Policy corpus updates | Daniel | Daniel | Mei (CS review) | Sarah | Quarterly review |
| SLM re-train | Daniel | Daniel | FDE (advisory on hyperparams) | Mei | Weekly cadence |
| MCP tool additions | Daniel | Daniel | Mei (CS) | Sarah | New tool = 1 paragraph in YAML |
| New customer team onboarding | Daniel + CEO | CEO | Mei (CS) | Sarah | $5/mo cost ceiling per team |
| Eval-set-in-CI changes | Daniel | Daniel | FDE (advisory) | Mei, Sarah | Threshold 0.05 |

**The pattern:** Daniel is R+A on 11 of 12 decisions. Mei is C on 5. Sarah is C on 2. CEO is A on 1 (the cost ceiling). FDE is C on 4 (advisory only) and I on the rest. **After the handoff, FDE is consulted, not responsible. The customer is in charge.**

---

## 6. The 5-question rubric, in 1 page (the artifact the customer prints)

> **Print this. Tape it to the wall. Run it every 30 days.**
>
> **5-Question "FDE Has Left" Test**
> Each stakeholder answers independently. A "yes" on all 5 = handoff is clean.
>
> 1. **What does the drafter do?** (1 sentence)
> 2. **How do you know it's working?** (the observable metric)
> 3. **What breaks first when it goes wrong?** (the failure mode)
> 4. **How do you fix it?** (the runbook link)
> 5. **What's the cost ceiling, and how do you know when you've hit it?** (the alert + the runbook link)
>
> If any answer is "I don't know," **fix the gap before the FDE exits.** Re-read the runbook section. Run the eval set. Page the on-call. The 5-question test is the gate; the runbook is the contract.

---

## 7. The pattern (generalized)

The handoff taught me 4 things that generalize:

1. **The handoff is the engagement.** Everything before the handoff is preparation. If the customer can't answer the 5 questions 30 days after I leave, the engagement wasn't done. The 5-question test is the rubric; the 2-week transition is the process; the 60-day check-in is the proof.

2. **The runbook is the contract.** It's not enough to ship the code; you have to ship the runbook too. The runbook is what survives the FDE's exit. A code repo without a runbook is a liability, not an asset.

3. **The "FDE silent on Slack" ceremony is non-negotiable.** The 3 days of FDE silence in week 12 is the test that the customer can operate without the FDE. Without it, the handoff is a vibe; with it, the handoff is a contract.

4. **Lane awareness > full-stack knowledge.** Mei doesn't need to know the cost ceiling; Daniel does. Sarah doesn't need to know the thumbs-up rate; Mei does. A clean handoff is when each stakeholder knows their lane and defers the rest to the right owner. **The 5-question test checks lane awareness, not full-stack knowledge.**

```
  ┌──────────────────────────────────────────────────────────┐
  │  THE HANDOFF LIFECYCLE                                    │
  │                                                          │
  │  Week 11: Knowledge transfer (10 hr, structured)          │
  │           Day Mon: Runbook walkthrough                    │
  │           Day Tue: Eval set + regression drill            │
  │           Day Wed: Cost model + on-call drill             │
  │           Day Thu: SLM retrain + multi-agent              │
  │           Day Fri: RACI review + 5-question test          │
  │                                                          │
  │  Week 12: Independent operation (5 hr, customer-led)     │
  │           Day Mon: Iteration cadence (Daniel solo)        │
  │           Days Tue-Thu: FDE silent on Slack               │
  │           Day Fri: 5-question test (FDE silent)           │
  │           Day Fri: FDE commits last PR + closes laptop    │
  │                                                          │
  │  Day +30: First 5-question check-in                      │
  │  Day +60: Second 5-question check-in                     │
  │  Day +90: Third 5-question check-in                      │
  │                                                          │
  │  If all 5/5 at day +90 → handoff is done.                │
  │  If any answer is "I don't know" → fix the gap.          │
  └──────────────────────────────────────────────────────────┘
```

---

## 8. References

- **The 5-question test**: derived from "The 12 Factor App" methodology + the Google SRE Book's "Operational Excellence" chapter. Adapted for FDE engagements.
- **The RACI matrix**: from the Project Management Institute (PMI) standard; adapted for AI service ownership.
- **The "FDE silent on Slack" ceremony**: inspired by the "bus factor" practice in DevOps, refined for FDE handoffs.
- **The PacificFreight runbook**: `course/ai-fde/phase-3-deployment/consulting/runbook.md` (12 pages, 8 sections).
- **The handoff notes**: this file.
- **The 60-day check-in template**: derived from the Google SRE "Post-Engagement Review" template + Stripe's "Post-Incident Review" template.
- **The 4 engagements' parallel data**: PacificFreight (this), Acme Analytics (Case Study #4's parallel engagement), and 2 other SMBs in the FDE's portfolio — same handoff pattern, different customers, same outcome.
