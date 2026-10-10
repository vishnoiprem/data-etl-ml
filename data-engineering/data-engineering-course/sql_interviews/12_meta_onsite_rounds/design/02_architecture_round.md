# Lesson 2 — The Architecture / Product-Sense Round (60-min)

> **Author:** Prem Vishnoi &lt;prem.vishnoi@example.com&gt;
>
> **Source:** [Interview101 (2026)](https://www.interview101.com/interviews/meta/data-engineer), [Tryexponent (2026)](https://www.tryexponent.com/guides/meta-data-engineer-interview), [PracHub (2026)](https://prachub.com/interview-guide/meta-data-engineer-interview-guide)

## Round format

- **Duration:** 60 min (the longest round)
- **Surface:** "Given a product goal, define metrics, design schema, and implement ETL SQL." One continuous exercise.
- **Difficulty:** the *hardest* round in the Meta DE loop per Interview101.
- **Evaluator signal:** end-to-end thinking — can you go from "what does the PM want?" to "the row is in the warehouse"?

The interviewer says "Build a real-time dashboard for the WhatsApp
Business Messaging team, surfacing per-business message volume and
7-day retention." You have 60 min. This is the round.

## The 5-step framework (the *only* one you need)

This is the same framework from Module 11 Lesson 5
(`05_meta_system_design_walkthrough.ipynb`). It works in 60 min on a
whiteboard because each step is 10-12 min.

1. **Product goal → 2-3 success metrics** (10 min)
2. **Schema that supports the metrics** (12 min) — fact + dims, named grain
3. **ETL SQL that loads the schema from raw event tables** (15 min) — idempotency, partition key, sort key
4. **Cost model** (8 min) — storage, compute, egress per 1M events
5. **Failure modes** (10 min) — late events, schema drift, idempotency, retries, backfill

If you skip step 5 you fail. The interviewer is grading "what breaks
at 10x" as much as the schema.

## Worked example — WhatsApp Business dashboard (Module 11.5 has the full notebook)

**Step 1: metrics**
- DAB: distinct business_id with ≥1 message sent per day
- 7-day retention: % of businesses active on day D who sent ≥1 message in the next 7 days
- Power-business rate: % sending ≥100 messages per week

**Step 2: schema**
- Fact: `fct_business_message_daily` (1 row / business_id / day)
- Dims: `dim_business` (SCD2 on `business_size`, `industry`), `dim_date`

**Step 3: ETL**
```sql
INSERT OR REPLACE INTO fct_business_message_daily
SELECT sender_id AS business_id,
       DATE(sent_ts) AS day,
       COUNT(*) AS n_messages,
       COUNT(DISTINCT receiver_id) AS n_unique_receivers
FROM   whatsapp_message
WHERE  DATE(sent_ts) >= DATE('now', '-30 days')
GROUP BY sender_id, DATE(sent_ts);
```

**Step 4: cost** — give a per-1M-events projection with named numbers (S3 $23/TB-mo, EMR $0.05/vCPU-hr, egress $0.09/GB). The exact dollar figure is less important than the *order of magnitude* and the ability to name the bottleneck at 10x. See Module 11's `notebooks/05_meta_system_design_walkthrough.ipynb` for a fully worked example.

**Step 5: failure modes**
- Late events: idempotency key = (business_id, day) → INSERT OR REPLACE
- Schema drift: CI test that compares `INFORMATION_SCHEMA.COLUMNS` against the contract
- Backfill: re-run over the affected date range; INSERT OR REPLACE handles dupes

## The 3 most-asked 2026 product surfaces (from Interview101)

| # | Surface | Source question | The killer follow-up |
|---|---------|-----------------|----------------------|
| 1 | **Reels performance** | "Design metrics + dashboard for Reels retention." | "What if the algorithm changes weekly?" |
| 2 | **Cross-platform user behavior** | "Build a unified analytics layer across FB/IG/WA." | "How do you de-dupe a user_id that appears on 2 platforms?" |
| 3 | **Ads Auction** | "Real-time bid optimization + historical campaign performance." | "How do you support both point-in-time and current-state queries?" |

## The killer follow-ups (and the answers)

1. **"What if the algorithm changes weekly?"** — SCD Type 2 on `dim_algorithm_version`. Every fact row carries `algorithm_version_id` so you can re-run historical metrics under the algorithm that was live at the time.

2. **"How do you de-dupe a user_id across platforms?"** — `dim_user` is the resolved identity. Each platform has a `platform_user_id`. Bridge table `user_identity_bridge(user_id, platform, platform_user_id, valid_from, valid_to)`. The user_id is a Meta-wide stable ID; platform_user_id is the per-platform one.

3. **"Time-travel vs current-state queries?"** — Two patterns:
   - SCD2 dim gives you point-in-time. Query the fact at `ts` joined to the dim valid at `ts`.
   - Current-state is `WHERE valid_to = '9999-12-31'`.
   - For ads auction, you keep BOTH the bid_history fact (immutable) AND a snapshot dim for "current campaign state." They serve different questions.

## The "what changes at 10x" question (asked at every Meta onsite)

You will get asked this. The 3 honest answers are:

- **Storage**: 1B events/day, 1KB/event, Parquet + ZSTD = 100GB/day raw, $700/mo. Still cheap.
- **Compute**: Spark daily batch stops fitting in 24h. Move to streaming (Kafka + Flink) for the top-N metrics.
- **Egress**: dashboard queries dominate. Pre-aggregate. Materialize. 10K queries/mo × 1MB = 10GB, $0.90/mo.

The senior move is to *name* the bottleneck at 10x, not just say "we scale."

## Common failure modes

- No metric → schema. You jump to "I'll create a users table" before the interviewer said what success looks like.
- Schema without grain. "One row per..." is the first thing the interviewer listens for.
- ETL without idempotency. "I'll run it daily" — what if it runs twice? What if a row arrives late?
- No cost story. "It scales" is not an answer. Numbers are.
- No failure modes. The interviewer stops you at 45 min: "what breaks?"

## What to study next

- **`03_leadership_round.md`** — the E5/E6 ownership round.
- **Module 11** — `05_meta_system_design_walkthrough.ipynb` for the live worked example.
- **Module 4 in `data_modeling/`** — `04_high_level_diagrams` for the schema reference.
