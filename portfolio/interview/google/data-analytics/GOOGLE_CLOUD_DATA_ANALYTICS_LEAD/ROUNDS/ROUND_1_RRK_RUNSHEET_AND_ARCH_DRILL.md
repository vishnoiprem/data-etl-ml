# RRK Run-Sheet and Live Architecture Drill

**Role:** Data & Analytics Lead, Google Cloud Consulting (Singapore) | **Round 1 RRK**, ~60 min, virtual
**Purpose:** fills three gaps the recruiter brief names that no other file covers: a minute-by-minute run-sheet, a "draw and defend" architecture drill, and the GCA answer routine.

> **Public repo.** No employer names, customer names or real figures in this file. Keep filled-in stories in a private, gitignored location.

---

## 1. Brief-to-file map (what to open for each theme)

| Brief section | Theme | Open |
|---|---|---|
| 2, 4c | Distributed-data correctness | `ROUND_1_RRK_TOPIC_DEEP_DIVE.md`, `..._BACKFILL_ATOMIC_PUBLISH_ANSWER.md` |
| 2 | Code review (practical element) | `..._CODE_REVIEW_DRILL.md`, `..._PART1_CODE_REVIEW_ANSWER.md` |
| 2 | Enterprise platform design (live) | **Section 3 below** |
| 4d | Executive influence, first 72 h | `..._EXECUTIVE_INFLUENCE_ANSWER.md`, `..._TROUBLED_ENGAGEMENT_ANSWER.md` |
| 4e | Utilisation, margin, pre-sales, competitors | `..._PRACTICE_COMMERCIAL_ANSWER.md` |
| 4f | People leadership | `..._PEOPLE_LEADERSHIP_ANSWER.md` |
| 4c | Governance, residency | `..._GOVERNANCE_ANSWER.md` |
| 5 | GCA | **Section 4 below** |

---

## 2. The 60-minute run-sheet

| Min | Likely block | Your move |
|---|---|---|
| 0-3 | Intro | 90-second pitch: scope, one outcome with a number, why this role. Stop. |
| 3-20 | Behavioural or technical depth | STAR, outcome first, "I" not "we", one honest miss |
| 20-40 | Practical element: code review or live design | Section 3. Restate, clarify, structure, then solve |
| 40-52 | Consulting, practice or people | Hypothetical framework (Section 4) |
| 52-60 | Your questions | Ask two (Section 5). Do not skip them |

**Timing rules**
- Answers: 2 minutes, then stop and let them probe.
- Restate the question in one sentence before answering (past scores show drifting to a different question).
- If a clarifying question gets no answer, say "I'll assume X" and move on.

---

## 3. Live architecture drill: draw and defend

The brief says you will "draw and defend an architecture" and reason about **correctness, scale, reliability, security, maintainability**. Use this fixed order every time.

### 3.1 Order of play (15 minutes)

| Step | Time | Say or draw |
|---|---|---|
| 1. Outcome and users | 2 | Who decides what with this data? What is the decision latency? |
| 2. Quantify NFRs | 2 | Volume, events/sec, freshness SLO, availability, retention, residency, cost ceiling, team skills |
| 3. Draw the spine | 4 | Sources -> ingest -> raw (immutable) -> curated -> serve -> consume, with governance as a vertical bar |
| 4. Walk one failure path | 3 | Late data, duplicate, poison message, schema change, backfill |
| 5. Security and cost | 2 | Write-path identity, perimeter, masking, quotas, cost guardrails |
| 6. Trade-offs and recommendation | 2 | Two options rejected, with the reason |

### 3.2 The spine on Google Cloud

```
Sources --> Pub/Sub / Datastream / Storage Transfer
              |
         Dataflow (stream + batch, event-time, dedup)   --> dead-letter topic
              |
   BigQuery raw (append-only, partitioned, ingest_ts)
              |
   Dataform / scheduled SQL (MERGE on business key, bounded window)
              |
   BigQuery curated (partitioned + clustered, authorised views)
              |
   Looker semantic layer / Vertex AI features / BI Engine
Governance bar: Dataplex (catalog, quality, lineage), policy tags + masking,
IAM least privilege, VPC Service Controls perimeter, CMEK, regional datasets
Ops bar: Cloud Monitoring SLOs, freshness + volume + null-rate checks, budgets + quotas
```

### 3.3 Defend each choice (one line each)

| Choice | Defence | Alternative and why not |
|---|---|---|
| Raw layer append-only | Enables replay, audit, backfill without touching the source | Update in place: loses history, makes rollback hard |
| Event-time windows plus allowed lateness | Correct on out-of-order data | Processing-time: wrong totals near boundaries |
| Idempotent MERGE on business key | Safe retries and restarts | Blind INSERT: duplicates on retry |
| Dead-letter topic | One bad record does not stop the stream | Fail the job: outage from one record |
| Write to staging, validate, then swap/publish | Consumers never see partial data | Write straight to prod table |
| Partition + clustering + `require_partition_filter` | Cost and speed under control | Full scans: bill and latency grow with data |
| VPC-SC perimeter plus column-level policy tags | Exfiltration and PII control | IAM alone: no exfiltration boundary |
| Regional dataset | Residency commitment | Multi-region default: may breach residency |
| Reversible cutover by view switch | Rollback is one statement | Big-bang cutover |

### 3.4 Six practice prompts (do each aloud in 15 min)

1. Retailer wants near-real-time inventory across hundreds of stores. Design it.
2. Bank migrating a legacy warehouse. Regulator requires data stays in-country.
3. Real-time fraud signals feeding an ML model (features online and offline).
4. Customer 360 merging online and offline identity.
5. Enterprise "chat with data" with row-level security.
6. Multi-country rollout: one platform, three residency regimes.

For each, finish with: **the one thing most likely to fail, how you would detect it, how you would roll back.**

### 3.5 Self-check after each drill

- Did I quantify NFRs before drawing?
- Did I name the failure path unprompted?
- Did I state who owns it after go-live (operating model)?
- Did I say how decommissioning of the old system happens?
- Did I give a recommendation, not "it depends"?

---

## 4. Hypothetical and GCA routine (the four steps)

| Step | Spoken template |
|---|---|
| Understand | "Let me restate: [one sentence]. Two questions: [scope], [constraint]. If unknown, I'll assume [A] and [B]." |
| Prepare | "I would want [data/metrics/artefacts], from [source], and I'd talk to [stakeholders]. Constraints: [list]." |
| Options | "Three options: [1], [2], [3]. Trade-offs on [cost, risk, time, readiness]." |
| Support | "I recommend [2] because [evidence]. Execution: [first 30 days]. Risks: [two]. Success measure: [metric, baseline, target]." |

**Consulting-specific add-ons:** first 30 days of a new programme (listen, baseline, align decision rights, quick win, governance cadence); first 72 hours of a troubled one (stabilise, diagnose by owner, options plus re-baseline).

---

## 5. Questions to ask at the end (pick two)

1. "What separates the practice leads who thrive here from those who struggle in the first year?"
2. "How is the practice balancing utilisation against investment in reusable assets today?"
3. "Which engagement type is growing fastest in the region, and where is delivery capacity tightest?"

---

## 6. Open items still blocking you

| # | Item | Note |
|---|---|---|
| 1 | The 13 `[TODO]` markers in `ROUND_1_RRK.md` | Each is a known probe point |
| 2 | **Employer inconsistency** | `ROUND_1_RRK.md` and the TODO list refer to an employer that does not appear on your current resume. Either add it to the resume or rewrite those answers using only resume-backed experience. A recruiter will compare the two |
| 3 | **Team-size inconsistency** | Resume says growth from 8 to 30; the answer bank says 8 to 25. Pick one true figure and use it everywhere |
| 4 | Google Cloud certification date | The brief says leaders are expected to get hands-on early |
| 5 | Run Google's Interview Warmup once | The brief links it |
| 6 | One live mock with someone who interrupts | Calibrates timing |

## 7. Resume-to-theme anchors (anonymised)

| Theme | Resume evidence to draw on (add real numbers privately) |
|---|---|
| Lakehouse modernisation | Legacy-to-lakehouse programme, multi-country, finance/supply chain/retail/e-commerce domains |
| Real-time | Streaming platform for logistics with event-time and low-latency serving |
| Regulated data | AML and entity screening across many jurisdictions; PDPA/GDPR |
| ML to production | Pricing, forecasting, route optimisation, item matching |
| GenAI | Text-to-SQL with semantic layer and guardrails |
| Leadership | Scaled a data organisation across four domain squads with outcome-linked KPIs |
