# Module 4 — Behavioral Questions for FDEs

> **Behavioral questions test whether you can survive the customer room.** A customer sits on the other side of most of the FDE job. The interviewer is deciding whether they can trust you in the room with one. **The signal: a candidate who names a real customer, a real disagreement, and a real resolution is showing they can do the work.**

---

## The 3 question types (every FDE behavioral question fits one)

### Type 1: Customer interaction

> "Tell me about a time you handled a difficult customer."
> "Tell me about a time the customer was wrong."
> "Tell me about a time you said no to the customer."

**The FDE-specific signal:** did you find a resolution, or did you "win"? FDEs don't win against customers; they find resolutions that respect both the customer's constraint and the system's constraint.

**The Phase 1-5 answer:** Engagement 8 — the cost ceiling breach. Sarah wanted the bill under $5/mo; Daniel wanted to disable the SLM. I ran the 3-week fix and gave Sarah the YAML she could defend in front of her CFO.

### Type 2: Disagreement with a stakeholder

> "Tell me about a time you disagreed with your manager."
> "Tell me about a time you disagreed with the customer."
> "Tell me about a time you pushed back on a requirement."

**The FDE-specific signal:** did you disagree AND ship? FDEs disagree; they also ship. The disagreement is the input; the shipping is the output.

**The Phase 1-5 answer:** Engagement 2 — the pivot. I told the legal-tech customer their data wasn't RAG-ready and walked away. Better to lose 2 weeks than ship a system that fails at week 11. (This is the only "I said no" answer in the portfolio, and it's the one interviewers remember.)

### Type 3: Ambiguity / no spec

> "Tell me about a time the spec was unclear."
> "Tell me about a time you had to make a decision without all the information."
> "Tell me about a time you set the spec yourself."

**The FDE-specific signal:** did you set the spec, or did you wait for one? FDEs set the spec (the eval set is the spec) when none exists. The interviewer is testing whether you can operate in ambiguity without checking in every 5 minutes.

**The Phase 1-5 answer:** Engagement 1 — PacificFreight's drafter had no eval set in week 1. I built the 30-row eval set before writing the prompt. The eval set is the spec; the prompt is the implementation.

---

## The STAR format (always)

Every behavioral answer uses the STAR format:

- **Situation** (1-2 sentences): The customer, the engagement, the timeline.
- **Task** (1 sentence): What you had to do.
- **Action** (3-5 sentences): What you actually did, with specifics.
- **Result** (1-2 sentences): The outcome, with a metric.

**The metric is the signal.** A senior FDE names a metric (35/35 tests, $4.09/mo, 10-question test). A junior FDE says "it went well."

**Example: Type 1 (Customer interaction)**

- **Situation:** PacificFreight's CS team (12 people) was using the drafter at 150 emails/day. By week 8, the bill was $25/week, 5x over the $5/month ceiling.
- **Task:** Bring the bill under $5/month without breaking the 79%+ thumbs-up rate.
- **Action:** I ran a 3-week fix: week 1, emergency throttle (tightened rate limit, disabled SLM); week 2, multi-tenant split (separated the e-commerce customer); week 3, SLM at 90% routing. The fix combined all 4 Phase 5 projects.
- **Result:** Final bill: $4.09/month, under the ceiling. Mei's thumbs-up rate stayed at 79%+. The fix was 3 design decisions, 2 PRs, 0 customer-facing downtime.

---

## The 3 question types (deeper)

### Type 1 deep-dive: customer interaction

| Sub-question | The Phase 1-5 answer |
|---|---|
| "Tell me about a time you handled a difficult customer." | Engagement 8: cost ceiling breach. (See above.) |
| "Tell me about a time the customer was wrong." | Engagement 1: Mei wanted the drafter to "always include the customer's name" — but Mei's customers were CS teams, not end customers. I pushed back; we changed the spec to "include the CS rep's name" instead. |
| "Tell me about a time you said no to the customer." | Engagement 2: the pivot. I said no to the legal-tech engagement because the data wasn't RAG-ready. (This is the "FDE walks away" story.) |
| "Tell me about a time you said yes to the customer when you wanted to say no." | Engagement 5: the handoff. I wanted to keep owning the system, but the customer (Daniel) was ready to take over. I said yes to the 6-week transition. |

### Type 2 deep-dive: disagreement with a stakeholder

| Sub-question | The Phase 1-5 answer |
|---|---|
| "Tell me about a time you disagreed with your manager." | Engagement 3: the postmortem. After the week 11 SEV-1, my manager wanted to add a manual review step. I disagreed; I added a circuit breaker instead. Manual review doesn't scale; a circuit breaker does. |
| "Tell me about a time you disagreed with the customer." | Engagement 2: the pivot. (See above.) |
| "Tell me about a time you pushed back on a requirement." | Engagement 1: Mei wanted a "drafts per minute" metric. I pushed back; we settled on "thumbs-up rate" because it measures the customer-facing outcome, not the throughput. |

### Type 3 deep-dive: ambiguity

| Sub-question | The Phase 1-5 answer |
|---|---|
| "Tell me about a time the spec was unclear." | Engagement 1: the eval set as spec. (See above.) |
| "Tell me about a time you had to make a decision without all the information." | Engagement 7: the region failover. AWS ap-southeast-1 went down at 03:14 SGT. I had to decide: failback or stay on Tokyo? I chose stay on Tokyo (manual decision, hysteresis) because failback is riskier than staying on the replica. The SLO was "minimize RTO," not "stay in Singapore for data sovereignty." |
| "Tell me about a time you set the spec yourself." | Engagement 5: the handoff. The customer (Daniel) didn't have a 5-question test for the next FDE. I wrote it. The 5-question test is now the rubric for the next 30 customers. |

---

## The 5 behavioral anti-patterns

1. **"I worked on a project that..."** without the customer name. FDEs name customers. Always.
2. **"I disagreed with X"** without the resolution. FDEs find resolutions; they don't "win."
3. **"It went well"** without a metric. A senior FDE names a metric. Always.
4. **"My team did X"** without "I did Y." The interviewer is testing you, not your team. Use "I" for the action; use "we" for the result.
5. **"I learned a lot"** as the closing line. The closing line is the metric. "$4.09/month, 35/35 tests, 79%+ thumbs-up" is the closing line.

---

## The "no experience" answer (if you've never been customer-facing)

If your background is SWE-only (no customer-facing title), use the "transferable signal" framework:

- **"I've never held a customer-facing title, but I've worked with internal stakeholders (PMs, designers, SREs) who were the customer for my work."**
- **The story:** pick a project where you had to gather requirements from a non-engineering stakeholder, deliver a system that met their needs, and iterate on feedback.
- **The metric:** name the metric from that project (latency drop, cost reduction, uptime improvement).

**The signal:** the interviewer is testing whether you can learn the customer-facing skill. The transferable signal is "I've done this with internal stakeholders; the customer-facing version is the same skill with higher stakes."

**The 4 transferable stories:**

1. **"Tell me about a time you handled a difficult stakeholder"** → Any project where you disagreed with a PM or designer on the spec.
2. **"Tell me about a time you said no"** → Any project where you pushed back on a requirement.
3. **"Tell me about a time the spec was unclear"** → Any project where you set the spec yourself.
4. **"Tell me about a time you shipped under pressure"** → Any project where you hit a deadline with a constraint.

---

## How to use this module

1. **Memorize the 3 question types.** Every FDE behavioral question fits one.
2. **Pick 1 Phase 1-5 case study per type.** You have 10 case studies; map them to the 3 types (with overlap).
3. **Practice the STAR format.** Time yourself: 3-4 minutes per answer.
4. **Rehearse with an AI assistant.** Have it score you on the 5 anti-patterns.
5. **Use the metric as the closing line.** "$4.09/month. 35/35 tests. 79%+ thumbs-up. 10/10 at the 90-day check." Pick the one that fits the question.

---

## The 5-question cheat sheet (the FDE-specific behaviorals)

| Question | Phase 1-5 answer | Metric |
|---|---|---|
| 1. Difficult customer | Engagement 8: cost ceiling breach | $4.09/month |
| 2. Said no to the customer | Engagement 2: the pivot | 2 weeks saved |
| 3. Disagreed with manager | Engagement 3: postmortem | 0 manual review steps added |
| 4. Spec was unclear | Engagement 1: eval set as spec | 30-row eval set in week 1 |
| 5. Made myself unnecessary | Engagement 10: principal handoff | 3 next FDEs, 10/10 at 90 days |

**Memorize these 5.** They're the answers to 80% of FDE behavioral questions.
