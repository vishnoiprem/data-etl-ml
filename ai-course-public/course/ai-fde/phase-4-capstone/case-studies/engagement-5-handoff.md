# Case Study 5 — The handoff: when the FDE leaves

> **TL;DR (1 page).** After 12 weeks, I handed the PacificFreight
> drafter to Daniel. The handoff took 2 weeks. The 5-question
> "FDE has left" test — answered by Daniel, Mei, and Sarah
> independently — confirmed the handoff was clean. **The lesson:**
> the handoff is the engagement. Everything before the handoff
> is preparation. If Daniel can't answer the 5 questions 30 days
> after I leave, the engagement wasn't done.

---

## The 5-question "FDE has left" test

I asked Daniel, Mei, and Sarah to answer these 5 questions
independently, 30 days after my last commit:

1. **What does the drafter do?** (1 sentence)
2. **How do you know it's working?** (the observable metric)
3. **What breaks first when it goes wrong?** (the failure mode)
4. **How do you fix it?** (the runbook link)
5. **What's the cost ceiling, and how do you know when you've
   hit it?** (the alert + the runbook link)

### Daniel's answers (the IT owner)

1. "Drafts replies to customer emails using RAG over our policy
   corpus and shipment data."
2. "The eval set runs every Monday at 09:00 SGT. Faithfulness
   stays above 0.85; thumbs-up stays above 70%."
3. "The retriever returns 0 chunks for a query (the corpus is
   empty for that shipment ID). Mei gets a generic draft and
   reverts it."
4. "Open the runbook, section 'retriever returns empty'. The fix
   is `docker restart rag` and `python3 admin/reindex.py`."
5. "$5/month. The Prometheus alert fires when the weekly bill
   exceeds $4."

### Mei's answers (the CS user)

1. "Drafts replies to customer emails so I don't have to write
   them from scratch."
2. "My thumbs-up rate. If it drops below 70%, something's wrong."
3. "The draft mentions the wrong shipment status (e.g., says
   delivered when it's held at customs). I revert and re-read
   the corpus."
4. "I tell Daniel. He re-runs the eval set and re-deploys if
   needed."
5. "I don't know — Daniel tracks the bill."

### Sarah's answers (the ops user)

1. "I don't use the drafter directly. I use the multi-agent
   dispatcher's summary for multi-shipment cases."
2. "The aggregate stats at the top of the daily ops review.
   If they drop, something's wrong."
3. "The dispatcher trace shows that an agent ran but produced
   empty output. I re-run the case."
4. "I tell Daniel. He checks the agent's circuit breaker."
5. "I don't know — Daniel tracks the bill."

## What this tells me

- **Daniel knows everything.** He can answer all 5 questions.
  ✓
- **Mei knows what she needs.** She knows the user-facing
  metrics (thumbs-up rate) and the failure modes she sees.
  She defers the IT questions to Daniel, which is correct.
  ✓
- **Sarah knows her lane.** She uses the dispatcher, not the
  drafter. She knows the user-facing metrics for her lane.
  She defers the IT questions to Daniel, which is correct.
  ✓

The handoff was clean. **All 3 stakeholders can answer their
  5 questions without me.**

## What I shipped for the handoff

### 1. The runbook

`course/ai-fde/phase-3-deployment/runbook.md` — 8 pages,
covering:
- **Overview** (system diagram, the 10 endpoints, the 13/13
  tests)
- **Daily ops** (the eval set, the iteration cadence, the
  rollback procedure)
- **Weekly ops** (the cost review, the corpus review, the
  SLM re-train)
- **Incident response** (SEV-1 playbook, the 3-tier fallback
  pattern, the public postmortem template)
- **On-call rotation** (who's on call, the escalation tiers,
  the contact info)
- **RACI** (who's Responsible, Accountable, Consulted,
  Informed for each decision)
- **Glossary** (every acronym, every tool, every metric)
- **5-question test** (the handoff rubric)

### 2. The eval set + the iteration cadence

`shared/eval_set.jsonl` (30 rows) + `service/eval.py` (4 RAGAS
metrics + regression check + markdown report). The iteration
cadence runs every Monday at 09:00 SGT.

### 3. The cost model

`shared/cost_model.md` (1 page) — the bill is $0.50/week at
current volume; the ceiling is $5/month; the alert fires at
$4/week.

### 4. The model card

`projects/03-distilled-slm/slm/model_card.md` — the SLM's
intended use, eval results, limitations, the operational
contract (rate limit, breaker, redaction, audit log).

### 5. The handoff notes

`course/ai-fde/phase-3-deployment/handoff-notes.md` (3 pages):
- **What I did** (the 12-week timeline)
- **What I didn't do** (the things I'd add with 4 more weeks)
- **What's likely to break first** (the 3 failure modes I'm
  most worried about)
- **Who to call when it breaks** (Daniel's phone, Mei's
  email, Sarah's Slack)
- **The 5-question test** (the rubric for the handoff)

## The 3 failure modes I'm most worried about

1. **The policy corpus goes stale.** If Daniel doesn't update
   the policy corpus when the Singapore customs rules change,
   the drafter will give outdated answers. Mitigation: Daniel
   owns the corpus; the iteration report flags "policy corpus
   age > 30 days" as a warning.
2. **The SLM's training data goes stale.** If Mei's style
   evolves, the SLM will drift. Mitigation: the SLM re-trains
   weekly (every Monday after the iteration cadence).
3. **The cost ceiling is hit.** If 5 customer teams start
   using the drafter, the bill will spike. Mitigation: the
   Prometheus alert fires at $4/week; Daniel investigates
   before hitting $5.

## The 60-day post-handoff check

I checked in at 30 days and 60 days. At 30 days:
- All 3 stakeholders answered the 5 questions correctly.
- The iteration cadence ran every Monday; faithfulness stayed
  above 0.85; thumbs-up stayed above 70%.
- The bill was $0.48/week, well under the ceiling.
- No SEV-1 incidents.

At 60 days:
- All 3 stakeholders still answered the 5 questions correctly.
- The iteration cadence ran every Monday; one regression was
  caught and rolled back on a Wednesday (the SEV-1
  postmortem is in `case-studies/engagement-3-postmortem.md`).
- The bill was $0.55/week, still under the ceiling.
- 1 SEV-1 incident, resolved in 38 minutes.

The engagement is in steady state. The customer is happy.
The FDE has left.

## Lessons

1. **The handoff is the engagement.** Everything before the
   handoff is preparation. If the customer can't answer the
   5 questions after you leave, the engagement wasn't done.
2. **The runbook is the contract.** It's not enough to ship
   the code; you have to ship the runbook too. The runbook
   is what survives the FDE's exit.
3. **The eval set is the gate.** The eval set runs every week;
   the customer knows what to do when it regresses.
4. **The cost ceiling is the spec.** The customer knows what
   "good" looks like (under the ceiling) and "bad" looks like
   (over the ceiling).
5. **The 60-day check-in is the proof.** I checked in twice
   after the handoff; both times the customer was in steady
   state. That's the test.

## Closing

This case study teaches the FDE how to leave. The 5-question
test is the rubric. The runbook is the artifact. The eval set
is the gate. The cost ceiling is the spec. The 60-day check-in
is the proof.

The PacificFreight engagement is in production. Mei uses the
drafter every day. Daniel owns the VM, the eval set, the
runbook, the SLM re-train, the on-call rotation. Sarah checks
the dispatcher trace on Monday mornings. The bill is $0.50/week.
The thumbs-up rate is 82%. The eval set is green.

**The FDE has left. The engagement is done.**