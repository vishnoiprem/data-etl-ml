# Lesson 35 — Design a Data Warehouse Schema for Instagram

> **Format:** mock interview transcript (~30 minutes).
> Read it aloud. Note the *hot user* problem, the
> *event volume vs storage* trade-off, and the
> *unbounded graph* modeling for follows.

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;

---

## Why this lesson

Instagram is an *engagement* warehouse at internet
scale. The interviewer is testing whether you can
reason about a 500B-events-per-day pipeline without
freezing — i.e., do you know the difference between
the *transactional fact* (every event) and the
*pre-aggregated rollup* (daily user-level metrics)?
Strong candidates walk in knowing that a "hot user"
(Justin Bieber, 300M followers) breaks naïve schemas,
that follower relationships are an *unbounded graph*
that doesn't fit a star schema, and that
"virality" is a *computed* measure, not a stored
column. This is a scale-and-aggregation round.

---

## The prompt

> Design a data warehouse for Instagram. 2B users,
> 100B photos, 500B events/day (likes, comments,
> views, story views). Analytics: engagement rate,
> story completion rate, content virality, creator
> monetization, ad performance.

---

## Step 1: Requirements gathering

Five clarifying questions:

1. **What is an "event"?** A *like*, a *comment*,
   a *view* (a post scrolled into the viewport for
   ≥3 seconds), a *story view*, an *ad impression*,
   a *click*, a *share*, a *save*. Each is a row in
   a stream. Do we need them all in the warehouse, or
   do we pre-aggregate some?
2. **What is a "user"?** A registered account, or
   also a logged-out visitor? (Instagram has
   logged-out traffic for SEO.) I assume registered
   users for the warehouse.
3. **What is "engagement rate"?** (likes + comments +
   shares + saves) / impressions, per post, per
   creator. Is the denominator *unique impressions*
   or *total impressions*? (It matters — a user
   scrolling past the same post 5 times is 5
   impressions, not 1.)
4. **Story completion rate.** A story is a sequence
   of frames (1-20). Is the rate "fraction of viewers
   who saw frame N" or "fraction who saw the last
   frame"? I assume the latter.
5. **Creator monetization.** Payouts from Instagram
   (bonuses, ad revenue share, badges, subscriptions).
   Is this in scope? I assume yes — it's a fact with
   its own dim.

---

## Step 2: High-level architecture

Three fact tables at three different grains:

```mermaid
fact_engagement_events  (grain: 1 row per engagement event)
   ── but stored pre-aggregated as fact_post_daily ──

fact_post_daily  (grain: 1 row per post, per day)
   ├── post_day_key      (PK)
   ├── post_key          → dim_post
   ├── creator_key       → dim_creator
   ├── date_key          → dim_date
   ├── impressions       (BIGINT)
   ├── unique_viewers    (BIGINT)
   ├── likes             (BIGINT)
   ├── comments          (BIGINT)
   ├── shares            (BIGINT)
   ├── saves             (BIGINT)
   ├── profile_visits    (BIGINT)
   ├── follow_attribs    (BIGINT, follows attributed to this post)
   └── engagement_rate   (REAL, computed)

fact_story_daily  (grain: 1 row per story-frame, per day)
   ├── story_frame_key   (PK)
   ├── story_key         → dim_story
   ├── creator_key       → dim_creator
   ├── date_key          → dim_date
   ├── frame_number      (INT, 1..20)
   ├── impressions       (BIGINT)
   ├── unique_viewers    (BIGINT)
   ├── completion_rate   (REAL, fraction who saw last frame)
   ├── tap_forward_count (BIGINT)
   ├── tap_back_count    (BIGINT)
   └── exit_count        (BIGINT)

fact_ad_impressions  (grain: 1 row per ad, per day, per
                       country, per age_band, per gender)
   ├── ad_day_key        (PK)
   ├── ad_key            → dim_ad
   ├── advertiser_key    → dim_advertiser
   ├── date_key          → dim_date
   ├── country_key       → dim_country
   ├── age_band_key      → dim_age_band
   ├── gender_key        → dim_gender
   ├── impressions       (BIGINT)
   ├── clicks            (BIGINT)
   ├── spend_usd_cents   (BIGINT)
   ├── ctr               (REAL)
   └── cpm_usd_cents     (REAL)
```

Dimensions:

- `dim_user` — SCD 1. user_id, username, signup_date,
  country, language, is_creator, is_verified,
  follower_count (current only).
- `dim_creator` — SCD 2. creator_id (= user_id for
  creators), category, monetization_enabled,
  payout_country, joined_creator_program_at.
- `dim_post` — SCD 1. post_id, creator_key, type
  (photo/video/reel/carousel), created_at, caption,
  hashtags (array), audio_id, is_sponsored.
- `dim_story` — SCD 1. story_id, creator_key,
  created_at, num_frames, audio_id.
- `dim_ad` — SCD 1. ad_id, advertiser_key, format
  (image/video/reel/story), objective (awareness/
  consideration/conversion), created_at.
- `dim_advertiser` — SCD 1. advertiser_id, name,
  industry, country.
- `dim_country` — small dim.
- `dim_age_band` — small dim (13-17, 18-24, 25-34,
  35-44, 45-54, 55+).
- `dim_gender` — small dim (male, female, nonbinary,
  unspecified).
- `dim_date` — conformed.

Note: there is *no* `fact_engagement_events` table
in the final warehouse — the raw event stream is
processed in a streaming pipeline (Flink, Spark
Streaming) that writes the pre-aggregated
`fact_post_daily` and `fact_story_daily` rollups.
The *warehouse* is the rollup; the raw events live
in a data lake (S3, HDFS) for ad-hoc ML and
reprocessing.

---

## Step 3: The 3 hardest parts

### 3.1 The hot-user problem (Justin Bieber scale)

A "hot user" is a user with disproportionately many
followers — Justin Bieber (~300M), Selena Gomez
(~400M), Cristiano Ronaldo (~600M). When they post:

- A single post generates *billions* of
  engagement events in the first hour.
- The rollup job for that post must aggregate
  billions of events into a single
  `fact_post_daily` row.
- The post's `creator_key` becomes a *hot partition*
  in the warehouse — every query "what's trending?"
  hits the same partition.

Three mitigations:

1. **Pre-aggregate at the streaming layer.** Don't
   wait for the warehouse to do the aggregation. The
   streaming job (Flink) maintains an in-memory
   counter per `(post_key, event_type)` and flushes
   to the warehouse every 5 minutes. The warehouse
   sees a stream of small updates, not a deluge at
   the end of the day.
2. **Sharded hot partitions.** If a single
   `creator_key` has >10M followers, the
   `fact_post_daily` row is sharded into N rows
   (`shard_key = 0..N-1`), and the rollup job
   picks `N` based on follower count. The analyst
   query sums across shards.
3. **Separate "viral post" fact.** For posts that
   cross a threshold (e.g., 1M impressions in 1
   hour), write a separate `fact_viral_post_hourly`
   fact at finer granularity (1 row per hour, not
   1 per day), so the dashboard can show
   real-time virality without scanning the daily
   rollup.

The interview question "what if a user has 600M
followers?" is testing whether you have thought
about hot partitions. Strong candidates say: "I'd
shard the rollup, pre-aggregate at the streaming
layer, and have a separate viral-post fact for
threshold-crossing posts."

### 3.2 Event volume vs storage

500B events/day × 365 days = 182.5T events/year. At
~200 bytes per event (user_id, post_id, event_type,
ts), that's ~36 PB/year of raw events. You cannot
put 36 PB in a star-schema warehouse. The right
architecture is:

```
Event stream (Kafka / Kinesis)
    ↓
Streaming processor (Flink / Spark)
    ├── writes raw events to data lake (S3 / HDFS)
    │     - parquet, partitioned by date
    │     - 36 PB/year, but cheap (~$0.02/GB/month)
    │
    └── writes pre-aggregated rollups to warehouse
          - fact_post_daily, fact_story_daily, etc.
          - 100B posts × 365 days = 36.5B rows/year
          - ~7 TB/year at 200 bytes/row
          - this is what the dashboard reads
```

The warehouse is the *summary*; the data lake is
the *raw record*. The split is by access pattern:

- *Dashboard / OLAP* (BI tools, finance, ops) —
  read from the warehouse, query latency in
  seconds.
- *Ad-hoc ML / reprocessing* (data scientists) —
  read from the data lake, query latency in
  minutes, much higher flexibility.

Strong candidates articulate this split clearly:
"The warehouse is the rollup; the lake is the
source of truth."

### 3.3 Unbounded graph: follower relationships

Instagram has 2B users and hundreds of billions of
follower edges. The "follower count" on `dim_user`
is *current* count only — it doesn't tell you "how
many followers did this user have on 2024-01-15?"

Three options:

- **`dim_user.follower_count` as SCD 1** — current
  count only. Cheap, but loses history.
- **`fact_follower_snapshot` as periodic
  snapshot** — one row per (user, day) with
  `follower_count`, `following_count`. With 2B
  users × 365 days = 730B rows/year. ~140 TB/year
  at 200 bytes/row. Possible but expensive.
- **`fact_follow_events` as transactional** — one
  row per (follower, followee, event_type,
  event_ts) with `event_type = 'follow' | 'unfollow'`.
  Much smaller (one row per follow/unfollow, not
  per day per user), but the *current* follower
  count requires a window function or a materialised
  view.

For a first-pass warehouse, I'd pick **option 2
(periodic snapshot)** for the *top 1% of users*
(those with >100K followers — the creators) and
*option 1* (SCD 1, current count) for everyone
else. The hot users are the ones the analyst
actually queries; the long tail of users with
<1000 followers doesn't need historical
attribution.

The "unbounded graph" is the modeling problem: a
follower relationship is a *bi-directional* edge
in a graph, and graphs don't fit the star schema
naturally. A strong candidate names this trade-off
explicitly: "I'm not modeling the full graph; I'm
modeling a *snapshot* of the graph for the
analytically-interesting users."

### 3.4 Virality calculation

"Virality" is a *computed* measure, not a stored
column. The simplest definition: the rate at which
impressions are growing over time. For a post
created at `t0`, virality at time `t` is:

```
virality(t) = d(impressions)/dt
            = (impressions_at_t - impressions_at_t-1h)
              / impressions_at_t-1h
```

The query is a self-join on `fact_post_hourly`
(filtered to the post) with a 1-hour lag. The
result is a time series, not a single number.

Stronger candidates also define "viral" as
*secondary engagement* — a user saw the post
because a *friend* engaged with it, not because
they followed the creator. That requires a
*referral* column on the engagement event
(`referred_by_user_key`), which is the
`fact_referral_engagements` fact. This is the
*true* virality measure and is what the
"Friends of friends" feed uses.

---

## Step 4: Common failure modes

1. **Putting 500B raw events in the warehouse.** This
   blows up storage and query cost. The warehouse
   is the *rollup*; the lake is the *raw record*.
2. **One row per post, not per (post, day).** A post
   that has engagement for 30 days has 30 rows in
   `fact_post_daily`, not one row with summed
   metrics. The day-grain allows time-series analysis
   and rollups by date.
3. **Storing `engagement_rate` as a column on
   `dim_post`.** It changes daily as engagement
   evolves. Compute it at query time, or store it
   in the daily rollup.
4. **No shard key for hot creators.** A celebrity
   post becomes a hot partition that kills
   dashboard performance. Shard by `creator_key`
   for creators above a follower threshold.
5. **Modeling the full follower graph as a star
   schema fact.** It doesn't fit. Use a snapshot
   for the top users and a current count for
   the long tail.

---

## Step 5: Scoring against the rubric

| Bucket | Score | Notes |
|---|---|---|
| **Clarifies the business** | 5/5 | Asked about event definition, user scope, engagement denominator, story completion, monetization. |
| **Picks a grain** | 5/5 | `fact_post_daily`, `fact_story_daily`, `fact_ad_impressions`. Defended each, explained why the raw event stream lives in the lake. |
| **Makes and defends tradeoffs** | 5/5 | Hot-user sharding, lake vs warehouse split, snapshot for top creators, virality as a computed measure. |
| **Talks while drawing** | 5/5 | Narrated every dim, every FK, every measure, every architectural choice. |

---

## In the interview, you would say...

> "500B events/day does not go in the warehouse. The
> raw event stream lands in a data lake; a streaming
> processor (Flink) pre-aggregates into
> `fact_post_daily`, `fact_story_daily`, and
> `fact_ad_impressions`. The warehouse is the rollup,
> the lake is the source of truth. For hot creators
> (Justin Bieber scale), I shard the rollup by
> `creator_key` and write a separate
> `fact_viral_post_hourly` for threshold-crossing
> posts. Followers are an unbounded graph; I model
> it as a periodic snapshot for the top 1% of users
> (creators) and a current count on `dim_user` for
> the long tail. Virality is `d(imps)/dt`, computed
> from `fact_post_hourly`, not a stored column."

---

*Author: Prem Vishnoi &lt;pvishnoi@avilx.com&gt;*
