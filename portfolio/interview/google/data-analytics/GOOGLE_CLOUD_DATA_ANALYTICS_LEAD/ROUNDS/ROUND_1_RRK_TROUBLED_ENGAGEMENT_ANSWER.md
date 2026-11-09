# RRK: Troubled Engagement, First 72 Hours

**Scenario:** Four weeks into a 6-month programme for a Singapore bank (MAS regulated, 800 TB on Teradata and Oracle moving to BigQuery and Vertex AI). Delivery is 3 weeks behind, the budget is 20% over, the CIO says "Google is not delivering", the GSI partner is blaming Google in front of the customer, the senior consultant is burnt out and may leave, and data owners have given no access for 2 weeks.
**Question:** What do you do in the first 72 hours (hours 0 to 24, 24 to 48, 48 to 72)? Use Understand, Prepare, Options, Recommend.
**Time:** about 5 minutes, then 1 minute for the follow-up.
**Pass signal:** governance, communication and options, not only a technical fix, plus a real insight about causes.

---

## 1. Short answer (the version that was supplied, kept for reference)

Hours 0 to 24: triage, stop the bleed, one war room, one owner, get data (milestones, defects, burn rate), talk to the CIO, partner lead and consultant separately. Hours 24 to 48: stabilise and communicate, interim fix, transparent status, no surprises. Hours 48 to 72: recovery plan, 2 to 3 options, recommendation, re-baselined timeline, governance to prevent recurrence. Follow-up: private conversation with the partner lead with evidence, agree a recovery plan, protect the customer, never blame in front of the customer.

Good skeleton, but generic: it would fit any troubled project. Missing:
- **The insight that changes the framing:** four weeks in, 3 weeks late, 2 weeks of no access. The access block may explain most of the slip. That makes it largely a customer-side dependency, which you show with a timeline, never as blame.
- **The access problem itself.** The answer never says how you'd unblock data owners at a MAS-regulated bank.
- **The burnt-out consultant** is a retention and context risk, not only a line item.
- **Concrete options** for the CIO, each with cost, risk and timeline.
- **"Stop the bleed"** is undefined. Say what it means (freeze non-critical work, stop effort burning on blocked tasks).

---

## 2. Improved answer

**Restate (10 s):** "A MAS-regulated bank, four weeks in, 3 weeks late, 20% over budget, the CIO unhappy, the partner blaming us, a burnt-out senior, and access blocked for two weeks."

### Understand (questions, or state assumptions)
- Is the end date hard (licence expiry, regulatory) or a target?
- What exactly is the 20% over: partner burn, unplanned scope, rework, our own effort?
- What access is blocked, for whom, since which request date, and why (approval process, risk concern, workload, unclear request)?
- What does the CIO mean by "not delivering": which deliverable or behaviour?

### The framing observation
"Two of the three weeks of slip line up with the access block. If the evidence confirms it, this is mostly a customer-side dependency. I'd say that to the CIO with a timeline and no blame, and own the part that is ours."

### Hours 0 to 24: listen, get facts, protect people
| Who | What I do |
|---|---|
| **Senior consultant (1:1, first)** | Listen; cut their load today; agree time off and a backfill. They hold the context, so retention is the first fire. |
| **Delivery lead and engineers** | What's done, blocked, the real velocity, rework. |
| **GSI partner lead (private)** | Their plan, staffing, burn, their version of events. No debate in front of the customer. |
| **CIO's delegate or programme manager** | Specific complaints and decision-makers. |
| **Data owners (one or two)** | Why access is stuck. |

**Data I pull:** plan versus actuals and burn-down; effort and cost by workstream and by party; the access-request log with dates and approvers; the SOW and change log; defect and rework log; the RAID log.
**"Stop the bleed":** freeze non-critical work and stop effort burning on blocked tasks, and set one war room with one accountable owner.
**Output by hour 24:** a one-page fact base: slip by cause (access, scope, rework, estimate), overrun by cause, and the access timeline.

### Hours 24 to 48: diagnose, unblock, align
- **Classify causes:** customer dependency, scope and estimate, partner delivery, our delivery and people. Quantify each in days and dollars.
- **Unblock access on the critical path** with the bank's data-governance owner: a **staged path**, with masked or synthetic data and a non-PII subset now, and full production access when approvals land. Frame the request in the bank's approval format, citing least privilege, VPC Service Controls, audit logging and Singapore residency, so approvers see lower risk.
- **Align the partner:** one fact base, one joint narrative, a "no blame in front of the customer" rule, and a RACI. If the partner is a cause, tell them privately, with evidence.
- **Pre-wire the CIO:** a short call: "Here are the facts; tomorrow I'll bring options. No surprises."

### Hours 48 to 72: options and a decision
| Option | What changes | Risk |
|---|---|---|
| **A. Re-baseline the date** | Unblock access by [date]; move the end date by the access-driven slip (about 2 to 3 weeks); change request only for access-driven cost | The date moves; needs sponsor acceptance |
| **B. Hold the date, cut scope** | Phase 1 is the critical domains and the licence-exit path; defer lower-value domains and Vertex AI use cases | Business value deferred |
| **C. Add capacity** | More GSI and Google consultants to compress | Cost rises, burnout risk, and capacity doesn't help while access is blocked |

**Recommendation: A and B together.** Unblock access under a named executive sponsor, re-baseline into waves, **protect the date for the critical wave**, defer the AI use cases, and raise a change request only for the access-driven cost. Don't choose C first.

**Ask the CIO for, with dates:** an executive sponsor to clear access within five working days; agreement to the staged access path; a weekly steering meeting with decision rights; a decision on the plan by [date].

**What I'd say to the CIO (60 seconds):**
> "We're 3 weeks behind. About [2] weeks come from access that hasn't been granted since [date]; the rest is [estimate and rework] that we own. The overrun is [x], from [causes]. I'll show you the timeline. My recommendation: unblock access through a staged path this week, protect the date for the critical wave, defer the AI use cases, and reset the plan with weekly demos. I need two things: a sponsor to clear access, and a decision on the plan by Friday."

### Governance to prevent recurrence
Weekly joint steering, a RAID log with owners, a defect SLA for the partner, a burn-rate alert, an **access-readiness gate** before any future mobilisation, and a short retrospective on why this wasn't caught in week two.

### How I'd measure recovery
Access granted by date; slip trend week on week; overrun by cause; defect rate; demo acceptance; partner commitments met; consultant retained; CIO confidence at the next steering meeting.

### What I won't do
Argue about fault with the CIO, add people before the blockage is removed, promise the original date, or let the partner and me contradict each other in front of the customer.

---

## 3. Follow-up: "The partner says it's Google's fault in front of the customer."

**Answer:** "In the room, I stay calm and don't rebut. I say: 'We'll work through the facts together and come back with a joint plan.' That protects the customer's confidence. Afterwards I speak to the partner lead privately, with the fact base and timeline: where we own a gap, I say so; where they do, I show the evidence. We agree one joint narrative, a recovery plan, and a rule that disagreements are settled before the customer sees them. If it repeats, I escalate through the commercial and governance channel with facts, not complaints. The aim is to keep a working partnership, because we still need their capacity, while keeping the quality bar non-negotiable."

---

## 4. Pass checklist

- [ ] Restate and ask clarifying questions (or state assumptions)
- [ ] Spot the access block as a probable main cause of the slip
- [ ] Talk to the right people separately, with the data you'd ask each for
- [ ] A staged, regulator-aware path to unblock access
- [ ] Look after the burnt-out senior in the first 24 hours
- [ ] Three options with cost, risk and timeline, and a recommendation
- [ ] A short CIO message and specific asks with dates
- [ ] Governance to prevent recurrence, and recovery measures
- [ ] Follow-up: private, evidence-based, united front, escalate on facts

## 5. Likely probes

| Probe | One-line answer |
|---|---|
| "The CIO wants the original date." | I'd show what the original date costs in scope and risk, and offer option B to protect the critical wave. |
| "What if data owners still refuse?" | Escalate through the executive sponsor with a risk-based request (masked data first), and record the dependency and its impact on the date. |
| "What if the consultant resigns anyway?" | A handover plan, knowledge capture and a backfill, and an honest conversation about what would change their mind. |
| "Who pays for the 20% overrun?" | Split by cause with evidence: access-driven cost goes through change control; our own overrun is ours; partner overrun is theirs. |
| "How do you avoid this next time?" | An access-readiness gate, joint governance from week one, and a burn-rate alert. |
