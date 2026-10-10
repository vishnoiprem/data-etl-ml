# Lesson 1 — The Data Modeling Round (60-min Whiteboard)

> **Author:** Prem Vishnoi &lt;prem.vishnoi@example.com&gt;
>
> **Source:** [Interview101 (2026)](https://www.interview101.com/interviews/meta/data-engineer), [Tryexponent (2026)](https://www.tryexponent.com/guides/meta-data-engineer-interview), [Glassdoor 2026](https://www.glassdoor.com/Interview/Meta-Data-Engineer-Interview-Questions-EI_IE40772.0,4_KO5,18.htm)

## Round format

- **Duration:** 45-60 min, white-board or Excalidraw
- **Surface:** one product brief, 5-15 min for clarifying questions, 30 min for the schema, 10-15 min for follow-ups
- **Evaluator signal:** grain clarity, SCD choice, partition strategy, scale story, "what changes at 10x"

The interviewer says "Design a star schema to track Instagram Reels
performance metrics across different recommendation algorithms."
You have 60 min. This is the round.

## The 5-step framework (use this on every prompt)

1. **Clarify the product surface** — what is the user action, what is the metric, what is the *grain* of one fact row.
2. **List the dimensions** — user, time, geography, device, content, algorithm, etc.
3. **List the facts** — one row per (grain) — be explicit about cardinality.
4. **Name the SCD type** for each slowly-changing dimension. Default: Type 2 for any dim with a history.
5. **Scale story** — what changes at 10x users, 10x events, 10x storage. Pick partition keys, sort keys, bucketing.

## The 5 most-asked 2026 questions

| # | Question | Surface | Dims | Fact grain |
|---|----------|---------|------|-----------|
| 1 | "Design a star schema to track Instagram Reels performance metrics across different recommendation algorithms." | Reels | user, time, algorithm_version, audio, hashtag | 1 row / (reel, viewer, time-bucket) |
| 2 | "Meta wants to build a unified data model for cross-platform user behavior analysis (FB, IG, WA)." | Cross-platform | user, platform, session, content, time | 1 row / (user, event, time) |
| 3 | "Design an event-driven data model for Meta's advertising auction system that supports real-time bid optimization + historical campaign performance." | Ads Auction | advertiser, ad_set, ad, user, time, auction_ts | 1 row / auction event + 1 row / impression |
| 4 | "Design a data model for a ride-sharing app like Uber. Walk through partitioning at scale." | Rideshare | rider, driver, city, time, trip | 1 row / trip + 1 row / trip_event |
| 5 | "An Instagram metric is dropping. Walk through your root-cause analysis, the data model that would support it, and the follow-up." | Investigation | per-metric | 1 row / (metric, time-bucket, segment) |

Source: [Interview101 2026](https://www.interview101.com/interviews/meta/data-engineer) (Q1, Q2, Q4, Q5) and [Aced 2026](https://www.aced.io/guides/meta-data-engineer-interview) (Q3 Ads Auction).

## What "good" looks like

From the Interview101 strong-answer guidance:

> Proposes a fact table with proper grain definition, uses Type 2 SCDs
> for algorithm parameters to maintain historical context, and designs
> bridge tables for many-to-many relationships.

Translated into the framework:

- **Grain in 1 sentence.** "One row per (reel, viewer, time-bucket)." The interviewer stops you if you can't.
- **SCD Type 2** for `dim_algorithm_version` (algorithm parameters change weekly; you must keep history).
- **SCD Type 1** for `dim_user` PII fields (just overwrite; no history).
- **Bridge tables** for many-to-many: `reel_hashtag_bridge`, `reel_audio_bridge`.
- **Partition key** is `event_date`, **sort key** is `(algorithm_version_id, user_id, event_ts)` — the algo version is the *filter dimension* for backfill queries, so it goes first.
- **10x story:** at 1B Reels/day, 5KB/row = 5TB/day raw. Parquet + ZSTD cuts that to 0.5TB/day. Roll up to 1-hour buckets in the mart.

## The 4 things Meta probes

1. **Grain.** If you can't name it, you fail. "One row per..." is the first 30 seconds.
2. **SCD choice.** Type 2 is almost always the answer. Know why: history matters for ML backfills, debugging, audit.
3. **Bridge tables.** Many-to-many is the most-missed thing. Hashtags, audiences, ad-sets-all-ads: bridge, not comma-list.
4. **Scale.** "What changes at 10x?" Partition, sort, bucketing, pre-aggregation. Name the numbers.

## Common failure modes (from Glassdoor 2026)

- No grain statement — you draw a bunch of boxes, the interviewer says "what's one row?"
- All Type 2 everywhere — SCD Type 1 has its place (PII, denormalized lookup data)
- No bridge table — you stuff hashtags into a comma-separated column on the fact
- No scale story — the schema is "fine" but doesn't tell the interviewer what changes at 10x
- No follow-up — you finish the diagram in 25 min and sit there

## Practice prompts (60-min timed)

1. Reels performance + recommendation algorithm (above)
2. Cross-platform unified user behavior (above)
3. Ads auction — real-time bid + historical campaign (above)
4. **E-commerce store** — products, orders, customers, inventory (Aced 2026)
5. **Notification system** for a Reddit-style app — backend + data model (Aced 2026)
6. **Movie theater ticketing** — end-to-end data store (Aced 2026)

Worked solutions to #4-6 are in `code/meta_modeling_solutions.md`.

## What to study next

- **`02_architecture_round.md`** — the system-design flavor of the product-sense round. The schema you design here will be loaded by the ETL you design there.
- **`code/meta_onsite_schemas.sql`** — the 5 worked schemas (Reels, cross-platform user behavior, Ads Auction, ride-share, metric drop) executable against SQLite.
- **Module 4 in `data_modeling/`** — `04_high_level_diagrams` for the dimensional-modeling reference.
