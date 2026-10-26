# Palantir — Forward Deployed Software Engineer (FDSE)

## Company Snapshot
- **HQ**: Denver, CO / NYC / London
- **FDE Team Size**: ~1,500+ FDSEs (largest FDE org in the world)
- **Comp**: Mid $145K–$175K base; Sr $185K–$215K; Staff $230K–$260K; Median TC ~$215K, Staff TC $415K+
- **What they deploy**: Foundry / AIP / Gotham onto customer sites (commercial + US/UK gov)
- **Travel**: 50–75% typical; less for on-site "embedded" with single customer

## Interview Process (5–7 rounds, ~6–9 weeks total)
1. **Recruiter screen** (30 min)
2. **Technical phone screen — coding** (60 min, HackerRank)
3. **Technical phone screen — object modeling** (60 min, live whiteboarding)
4. **On-site loop (virtual or London/Denver)** — 4–5 back-to-back sessions
   - Coding round 2
   - Object modeling round 2
   - System design / "build a Foundry workflow" case
   - Behavioral / values
   - Bar-raiser with senior FDSE
5. **Final loop with hiring manager + skip-level**

---

## ✅ SUCCESS STORIES (candidates who got offers)

### Round 1 — Recruiter screen (30 min)
**Q:** "Walk me through a deployment you led. What was your specific contribution — not the team's?"
**A (winner):** *"I was the only engineer embedded at a regional hospital for 4 months. I owned the FHIR→Foundry pipeline single-handedly. I made 3 architecture decisions that mattered: (1) chose incremental CDC over batch ETL because the hospital couldn't tolerate nightly downtime, (2) wrote a custom loss in AIP to handle ~12% dirty data without re-labeling, (3) shipped a clinician-facing app in week 6 that the CMO actually used in his morning rounds. The system is still in production 14 months later."*
**Why it worked:** Concrete scope ("only engineer", "4 months", "FHIR→Foundry pipeline"), specific technical choices, business outcome (CMO used it), measurable longevity (14 months in prod). Showed founder-style ownership of a deployment, which is the FDSE DNA.

---

### Round 2 — Coding phone screen (60 min)
**Q:** *"Given a stream of events from N sensor sources, each with a timestamp and a sensor_id, find the top-K most active 10-minute windows."*
**A (winner — pseudocode sketch):**
```python
from collections import defaultdict, deque
def topk_windows(events, k, window_sec=600):
    by_sensor = defaultdict(deque)
    counts = defaultdict(int)
    res = []
    for e in events:
        ts, sid = e.t, e.id
        by_sensor[sid].append(e)
        # evict old
        while by_sensor[sid] and ts - by_sensor[sid][0].t > window_sec:
            by_sensor[sid].popleft()
        counts[ts] += 1  # rolling count per timestamp
        if len(by_sensor[sid]) == 1:
            counts[ts] = sum(len(d) for d in by_sensor.values())
        # maintain heap of top-K windows ...
    return heapq.nlargest(k, counts.items(), key=lambda x: x[1])
```
Then: *"I'd push back on the question — at Palantir scale this becomes a Foundry pipeline problem with time-bucketing, not a single-machine problem. I'd rather design it as a streaming analytic than a one-shot algo."*
**Why it worked:** Working code, then correctly reframing as a Foundry/pipeline problem (which is what FDSEs actually ship). Shows the candidate thinks in systems, not algorithms.

---

### Round 3 — Object modeling (60 min, whiteboarding)
**Q:** *"Design the data model for managing the UK NHS's COVID vaccination program — 50M patients, 5,000 clinics, 12 vaccine types, multi-dose scheduling, supply-chain constraints."*
**A (winner):**
- **Entities**: `Patient`, `Clinic`, `VaccineBatch` (with `manufacturer`, `lot`, `expiry`), `Appointment`, `DoseAdministration`, `AdverseEvent`
- **Key relationships**:
  - `Patient` 1—* `DoseAdministration` *—1 `VaccineBatch`
  - `VaccineBatch` *—1 `Clinic` (current location, with `transfers` audit log)
  - `Appointment` belongs to `Patient` AND `Clinic`, has `scheduled_dose_n`
- **Smart choices**:
  1. Make `VaccineBatch.lot` **immutable + append-only** with full lineage (critical for recalls — think PALANTIR's FDA audit use cases).
  2. Use a **typed event log** (`DoseEvent` with `kind`, `payload`) for any state change so we can replay history.
  3. Model **supply as a constraint**, not a field: clinics have `min_stock`, `reorder_threshold`, and a derived `days_of_supply` time series.
- **Pre-emptively defended trade-offs**: *"I'm splitting identity from demographics so we can re-issue patient IDs without rewriting the appointment graph — this matters when the NHS merges trusts."*
**Why it worked:** Modeled the actual domain (Palantir's bread and butter is regulated/clinical), used immutable/append-only patterns (Palantir favors these), showed awareness of audit + supply graph theory. Did NOT spend time on UI.

---

### Round 4 — System design / Foundry case (90 min)
**Q:** *"A port operator wants us to deploy Foundry to reduce container dwell time from 7 to 2 days. Walk me through the first 6 weeks."*
**A (winner — structured):**
- **Week 1 — Discovery**: shadow ops floor; map current TOS (terminal operating system) data flows; identify the 3 decisions causing dwell (gate assignment, customs hold, empty-return).
- **Week 2 — Data model + first ontology**: build the *Container*, *Vessel*, *Truck*, *CustomsHold* objects and 8 semantic links. Sample on real but non-prod data.
- **Week 3 — Pipeline**: ingest AIS (vessel) feeds, gate scan, customs feed via Kafka → Foundry dataset. Build data health dashboards.
- **Week 4 — First decision app**: an AIP-powered "dwell risk scorer" that flags containers likely to miss gate cutoff; tested against 2 weeks of back-data.
- **Week 5 — Pilot**: 1 berth, 30 containers/day, end-to-end app with the ops supervisor.
- **Week 6 — Rollout plan + handoff**: train 4 power users; document SOPs; transition to a long-tail backlog.
- **PM metrics**: dwell time, % containers flagged, false-positive rate, user MAU.
**Why it worked:** Concrete week-by-week plan; matched how Palantir actually runs pilots; explicit success metrics; flagged the user-adoption risk; ended with *handoff* (FDSEs hand off, not stay forever).

---

### Round 5 — Behavioral / Values
**Q:** "Tell me about a time you disagreed with your PM about a technical decision. What did you do?"
**A (winner):** *"We disagreed on whether to ship a real-time recommendation pipeline in week 1 or wait for evals. I wrote a 1-page decision doc listing the user-facing harm of being wrong (lost trust, churn) vs the cost of waiting (2-week delay). I got 2 senior engineers to read it independently. Then I talked to the PM, conceded the data-side concerns, and proposed an MVP that deferred 30% of the work. He agreed. We shipped in week 2 instead of week 1; we had zero P0 incidents in the first month."*
**Why it worked:** Disagreement framed as collaborative, principled, and resolved. Brought receipts (decision doc, external validation). Showed willingness to ship AND to slow down.

---

## ❌ REJECTION STORIES (candidates who didn't get offers)

### Rejection #1 — Object modeling round
**Q:** *"Model an airline's loyalty program."*
**A (loser):** *"So I'd start with a `User` class with email and points. Then a `Flight` class. There's a `Booking` connecting them. For status tiers I'd use an enum... Maybe ML on the side for personalizing offers..."*
**Why it failed:** Generic OO, no domain reasoning, no awareness of Palantir's "ontology" style (objects + links + functions), no edge cases (expiry, tier-matching logic, partner redemptions).
**What they should have said:** Lead with an *ontology* framing — `Member`, `Account`, `Tier`, `Partner` (airline, hotel, retailer), `MileAccrualEvent`, `MileRedemptionEvent`. Discuss points as an append-only ledger (immutability). Surface *the* hairy rules: tier-qualifying miles vs redeemable miles, expiry windows, partner conversion rates.

---

### Rejection #2 — Deployment case
**Q:** *"How would you deploy AIP for an oil & gas customer?"*
**A (loser):** *"I'd integrate AIP with their SAP and build a RAG pipeline. We'd do a PoC in 4 weeks."*
**Why it failed:** No discovery phase, no mention of safety/regulatory constraints, no ops handoff, no measurement plan, mistook "AIP" as just RAG.
**What they should have said:** Discovery with HSE + IT + ops first; data audit (well sensor data is dirty + sparse); AIP first app = safety-incident summarization with human-in-loop; explicit 6-week milestone with measurable adoption; plan for SCADA integration + offline-mode.

---

### Rejection #3 — Behavioral
**Q:** "Tell me about the hardest engineering problem you solved."
**A (loser):** *"I optimized a SQL query from 30 seconds to 0.5 seconds by adding an index."*
**Why it failed:** No customer/business context, no stakeholder management, single dimension (perf, not scope).
**What they should have said:** Frame it as *"I led the redesign of our batch reconciliation system for a Tier-1 bank. The query slowdown was a symptom — the real problem was the team's data model couldn't survive a regulatory audit. I rebuilt it, shipped in 11 weeks, and the bank's auditor signed off on our first attempt."*

---

## 📚 Reading List for Palantir FDSE Prep
1. Palantir blog — *"Foundry ontology primer"* (official)
2. Brennan McEachen (former FDSE) — *"So you want to be a Forward Deployed Engineer"* (Medium)
3. Vinoo Ganesh — *"The Definitive Guide to Forward Deployed Engineering"*
4. J.D. Maddox — *"My First 6 Months as a Palantir FDSE"* (Medium)
5. levels.fyi Palantir FDSE interview debriefs (search by date)
6. YouTube: *"Palantir FDSE mock interview — object modeling"* (multiple)
7. r/MachineLearning and r/cscareerquestions threads tagged "Palantir"
