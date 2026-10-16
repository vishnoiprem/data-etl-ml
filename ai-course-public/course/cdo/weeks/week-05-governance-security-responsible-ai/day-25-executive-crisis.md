# Lesson 25: Executive crisis

> **Week 5 · Day 25 · 90 min**
> **Deliverable:** The crisis playbook — detection, war-room, comms, post-mortem.

## 🎯 Architect Level
Staff.

## 🧠 Concept

Every CDO will face a crisis. The most common are:

- **Data breach** — PII or credentials leaked
- **Wrong number in the board deck** — financial, customer, or operational
- **Model failure** — a model in production produces biased, harmful, or wrong output
- **Vendor incident** — a key vendor (cloud, SaaS, model provider) has an outage
- **Regulator inquiry** — the regulator sends a letter or shows up
- **Public incident** — a journalist, customer, or employee goes public

The CDO who has rehearsed the crisis handles it. The CDO who hasn't, escalates badly, communicates late, and loses the room.

The crisis playbook has 5 phases:

| Phase | Time | What to do | Who does it |
|---|---|---|---|
| **1. Detect** | 0-15 min | Alert fires; on-call acknowledges; severity assessed | On-call + observability |
| **2. Triage** | 15-30 min | Severity 1/2/3 declared; war-room convened | Incident commander (most senior) |
| **3. Contain** | 30 min - 4h | Stop the bleeding; isolate the system; preserve evidence | War-room |
| **4. Communicate** | Concurrent | Internal (CEO, board, BU heads); external (regulator, customers, press) | Comms lead + legal + CEO |
| **5. Post-mortem** | 1-14 days | Blameless review; root cause; action items with owners; comms | CDO + war-room |

The single biggest mistake is to **communicate late**. Silence is interpreted as cover-up. The first communication should come within 60 minutes of the incident being declared, even if the message is "we are aware and investigating."

The second biggest mistake is to **not have a comms lead**. The CDO should not be drafting the customer email. The CDO should be running the war-room. The comms lead (often a comms exec or the chief of staff) handles the messaging.

The third biggest mistake is to **skip the post-mortem**. The post-mortem is where the organization learns. Blameless, structured, action items with owners and dates. Without it, the same incident happens in 6 months.

## 🛠️ Build It

**Spec:** Build the crisis playbook for the retailer. Cover 4 scenarios: data breach, wrong number, model failure, vendor outage.

**Acceptance:**
- 5 phases × 4 scenarios
- Comms templates for each
- Decision rights (who declares, who communicates, who escalates)
- 1 paragraph on the trade-off (transparency vs. legal exposure)

**Starter:** Use Day 23's breach response. Extend to the 3 other scenarios.

**Solution (crisis playbook, abridged):**

**Scenario 1: Data breach** — see Day 23.

**Scenario 2: Wrong number in board deck**

| Phase | Action | Owner |
|---|---|---|
| Detect | CDO notices before the meeting; or BU head flags during | CDO |
| Triage | Severity 1 (board meeting) or 3 (internal report) | CDO + CEO |
| Contain | Stop the deck; correct the number; re-issue | CDO + comms |
| Communicate | CEO addresses the board in-meeting; written correction within 24h | Comms + CDO |
| Post-mortem | How did the wrong number get in? What controls missed it? | CDO |

**Scenario 3: Model failure (e.g., biased credit decision)**

| Phase | Action | Owner |
|---|---|---|
| Detect | Customer complaint, regulator letter, or monitoring alert | ML on-call + risk |
| Triage | Severity 1 if material harm; Severity 2 if isolated | CDO + CRO + legal |
| Contain | Disable the model; revert to rule-based | ML on-call + risk |
| Communicate | Internal: CEO + board; external: customers + regulator | Legal + comms + CDO |
| Post-mortem | Bias test failure? Data drift? Feedback loop? Action items | CDO + CRO |

**Scenario 4: Vendor outage (e.g., cloud region down)**

| Phase | Action | Owner |
|---|---|---|
| Detect | Vendor status page + internal observability | Platform on-call |
| Triage | Severity 1 if customer-facing; Severity 2 if internal | CDO + CTO |
| Contain | Failover to secondary region; degrade to read-only if needed | Platform + SRE |
| Communicate | Internal: CEO + BU heads; external: customers (per SLA) | Comms + CTO |
| Post-mortem | RTO vs. RPO met? Vendor SLA honored? Internal gaps? | CTO + CDO |

**Comms template (Severity 1):** "At [time], [company] identified [issue]. We are [responding / investigating / resolving]. The impact is [scope]. Customer data [is / is not] affected. We will provide an update by [time]. For questions, [contact]."

**Decision rights:** CDO declares + leads. CEO communicates to board. CISO + legal handle regulator. Comms handles customers + press. CRO handles customer impact.

## 🏛️ Architect Notes

- **Trade-off:** Speed vs. accuracy. Communicate fast with what you know; correct later. Silence is the worst option.
- **Capacity / cost:** A crisis playbook is a document + a rehearsal. The rehearsal (quarterly tabletop) is the expensive part.
- **When NOT to use:** Don't draft a comms template for a crisis you're currently in. The template is for next time; for this time, get the war-room running.
- **Production checklist:**
  - [ ] 5 phases named
  - [ ] 4 scenarios covered
  - [ ] Comms templates
  - [ ] Decision rights named
  - [ ] Rehearsal cadence (quarterly)
  - [ ] Post-mortem process

## 🌙 Reflect

- Which scenario scares you the most? Why? Pre-write the answer.
- Who would you call first if a model failed in production right now?
- Write 3 sentences you'll say out loud tomorrow.

---

**Next:** Case Study 5 — The Margin Incident.