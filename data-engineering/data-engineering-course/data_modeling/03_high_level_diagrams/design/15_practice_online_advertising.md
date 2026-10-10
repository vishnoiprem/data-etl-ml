# Lesson 15 — Practice: Online Advertising Platform

> **What you'll learn:** the ad-tech star — an event-grain fact
> for impressions, clicks, and conversions, with campaign and
> creative as dimensions and CPM/CTR/CVR as the headline
> measures. By the end of this lesson you'll be able to draw an
> ad-tech warehouse for Google Ads, Meta Ads Manager, or The
> Trade Desk in under 15 minutes.

---

## The prompt

> "Design a data warehouse for an online advertising platform
> (think Google Ads, Meta Ads, or The Trade Desk) so the
> analytics team can answer questions about campaign
> performance, creative effectiveness, and ROI for
> advertisers."

This is the canonical ad-tech question. The trick is that
"advertising data" is actually three event types — impression
(ad shown), click (user clicked), conversion (user did the
desired action) — at the same grain (one event per ad
served), and the analyst's job is to compute ratios across
them (CTR, CVR, CPM) in every dashboard. The right model
makes those ratios trivial to compute; the wrong model
makes them 5-table joins.

---

## The star schema

```
                ┌──────────────┐
                │ dim_advertiser│
                │ (SCD 2)      │
                └──────┬───────┘
                       │ advertiser_key
                       ▼
┌──────────┐    ┌──────────────┐    ┌──────────────┐
│ dim_date │◄───┤  fact_ad_    ├───►│ dim_campaign │
│          │    │   events     │    │  (SCD 2)     │
└──────────┘    │              │    └──────┬───────┘
                │ measures:    │           │
                │  impressions │    ┌──────┴───────┐
                │  clicks      │◄───┤ dim_ad_      │
                │  conversions │    │   group      │
                │  cost_usd    │    │  (SCD 2)     │
                │  revenue_usd │    └──────────────┘
                └──────┬───────┘
                       │
                  ┌────┴────────┐
                  │dim_event_   │
                  │  type       │
                  └─────────────┘

                       ▲
                       │
                ┌──────┴───────┐    ┌──────────────┐
                │  dim_device  │◄───┤ dim_creative │
                │   type       │    │              │
                └──────────────┘    └──────────────┘
```

Nine tables. One fact, eight dimensions. The fact is the
*event* — every impression, click, and conversion is a row.

---

## Why an event-grain fact (and not three facts)

The temptation is to model three facts: `fact_impressions`,
`fact_clicks`, `fact_conversions`. The reason: the events
have different cardinalities (many impressions per click,
many clicks per conversion) and different semantics
(impressions are server-side; clicks are client-side;
conversions are post-attribution).

The right answer is **one fact, with an `event_type` column
and a `count` measure.** The reasons:

1. **Same grain.** Every event is "one ad served to one
   user at one time." The grain is identical. Different
   grains want different facts; same grain wants one fact.
2. **One row per event keeps the attribution path intact.**
   A click belongs to a specific impression; a conversion
   belongs to a specific click. If clicks and conversions
   are in separate facts, the analyst has to reconstruct
   the path with self-joins. With one fact, the path is
   `event_id` + `parent_event_id` (or a session key).
3. **The ratios are the headline measures.** CTR is
   `clicks / impressions` — that's a `WHERE event_type
   IN ('click')` vs `WHERE event_type = 'impression'`,
   both over the same fact. CVR is `conversions / clicks`
   — same pattern. With three facts, the ratio is a join
   across facts. With one fact, the ratio is a `CASE WHEN`
   in the same scan.

The fact has the following measures (each row contributes
to one):

| Measure | Type | Notes |
|---|---|---|
| `impressions` | INT | 1 if event_type = 'impression', else 0. |
| `clicks` | INT | 1 if event_type = 'click', else 0. |
| `conversions` | INT | 1 if event_type = 'conversion', else 0. |
| `cost_usd` | REAL | What the advertiser paid for this event. |
| `revenue_usd` | REAL | What the platform earned (CPM × impressions / 1000 for impressions; CPC for clicks; CPA for conversions). |

The three flag measures (`impressions`, `clicks`,
`conversions`) are 0/1 columns. They let the analyst
`SUM(impressions)`, `SUM(clicks)`, `SUM(conversions)` in
one pass without a `CASE WHEN`. The cost and revenue are
the financial measures that roll up to the campaign and
advertiser levels.

---

## The grain: one row per event

The grain is **one row per (ad, user, event_type,
timestamp)**. For an ad served 1000 times to 1000 unique
users, you get 1000 rows. The same ad served to the same
user twice (which is common — retargeting) is two rows.

If two events happen at the exact same timestamp
(impression + click in the same millisecond — possible
but rare), the grain becomes one row per
(ad, user, event_type, timestamp) and they're separate
rows.

The de-dupe question: do you ever have duplicate rows? In
a well-instrumented ad system, no — the event_id from
the ad server is unique. If you find yourself with
duplicates, the source has a bug, not the schema.

---

## The dimensions

### `dim_advertiser` (SCD Type 2)

The advertiser is the customer of the ad platform. They
change plans (spend caps, agency-of-record) and billing
terms. SCD 2 is mandatory — "what was this advertiser's
monthly budget when they ran this campaign in March?" is
a daily question.

### `dim_campaign` (SCD Type 2)

A campaign is a *bounded* advertising effort: a budget, a
start date, an end date, a target audience, a set of
creatives. Campaigns change mid-flight (the advertiser
raises the budget, swaps a creative, narrows the
targeting). SCD 2 captures the history so "spend by
campaign by day" is accurate to the campaign version
that was live on that day.

### `dim_ad_group`

Beneath the campaign is the ad group (Google's term) or
ad set (Meta's term). An ad group is a set of creatives
targeting a specific audience, with its own bid and
budget. SCD 2 because ad groups also get paused,
re-budgeted, and re-targeted mid-flight.

A campaign 1—* ad group 1—* creative. The fact is at
the ad-group-and-creative grain. (Some platforms model
the fact at the ad-group grain, with `creative_key` as a
denormalized FK; the choice is yours. We denormalize.)

### `dim_creative`

A creative is the actual ad — an image, a video, a
headline, a destination URL. SCD 1 — once a creative is
approved, its content doesn't change. (The *ad group* it
belongs to changes; the creative itself is fixed.)

### `dim_device_type`

Mobile, desktop, tablet, connected TV (CTV), audio.
Critical because CPMs differ 3–5x between mobile and
CTV. SCD 1.

### `dim_event_type`

The five-or-so values: `impression`, `click`,
`view_through_conversion`, `click_through_conversion`,
`engagement`. A small dim so the analyst can attach
attributes (e.g., `is_engagement_signal`, `is_chargeable`)
without re-typing.

### `dim_date`

The standard conformed date dim. Ad dashboards are
time-series first: "spend by day by campaign for the
last 30 days" is the canonical query.

---

## Why CTR, CVR, CPM, and ROAS are measures, not derived

The candidate trap: leave CTR/CVR/CPM off the fact and
compute them as `clicks/impressions` at query time. The
problem is *which impressions* — total impressions, unique
impressions, viewable impressions, eligible impressions?
A click is unambiguous; an "impression" is fuzzy.

The right move: store the *count* of each event type on
the fact (the 0/1 flag columns), and let the analyst
compute the ratio with a `WHERE` or `CASE WHEN` over the
same scan. The ratio is a query, not a measure, because
the denominator depends on the question.

The exception: **CPM** (cost per mille, i.e., per 1000
impressions) and **ROAS** (return on ad spend, i.e.,
revenue / cost) are useful as pre-computed measures on a
*campaign rollup* table, not on the event fact. The
campaign rollup has one row per campaign per day, with
`impressions`, `clicks`, `conversions`, `cost_usd`,
`revenue_usd`, `cpm`, `ctr`, `cvr`, `roas` as columns. The
event fact feeds the rollup; the analyst queries the
rollup for dashboards.

The "two tables" pattern is common: a row-level event
fact for deep dives, and a daily campaign rollup for
dashboards. The rollup is built by the ELT job, not by
the analyst.

---

## The advertiser hierarchy

```
Advertiser (the customer of the ad platform)
   └── Agency (optional — the agency-of-record)
        └── Campaign (a bounded ad effort)
             └── Ad Group (a set of creatives + targeting)
                  └── Creative (the actual ad)
```

The fact is at the ad-group + creative grain. The
hierarchy is *denormalized onto the fact*: the fact has
FKs to `dim_advertiser`, `dim_agency`, `dim_campaign`,
`dim_ad_group`, `dim_creative`. The denormalization is
justified by query speed (every dashboard joins all five)
and by the fact that the hierarchy is small (a campaign
has 1–10 ad groups, an ad group has 1–20 creatives).

A snowflaked version would have the hierarchy in
separate dim tables, with the fact joining only the
lowest level. The senior candidate explains the
tradeoff: denormalized wins on speed; snowflake wins
on storage. For a query-heavy ad platform, denormalized
wins.

---

## Worked query — CTR and CVR by campaign, last 30 days

```sql
SELECT
    c.campaign_name,
    SUM(f.impressions) AS impressions,
    SUM(f.clicks)      AS clicks,
    SUM(f.conversions) AS conversions,
    ROUND(1.0 * SUM(f.clicks) / NULLIF(SUM(f.impressions), 0), 4) AS ctr,
    ROUND(1.0 * SUM(f.conversions) / NULLIF(SUM(f.clicks), 0), 4) AS cvr
FROM fact_ad_events f
JOIN dim_campaign c ON f.campaign_key = c.campaign_key
JOIN dim_date     d ON f.date_key     = d.date_key
WHERE d.date >= DATE('now', '-30 days')
GROUP BY c.campaign_name
ORDER BY ctr DESC;
```

This is the canonical ad-tech dashboard query. The
measures are on the fact as 0/1 flags; the ratios are
computed in the same scan.

---

## Worked query — ROAS by advertiser

```sql
SELECT
    a.advertiser_name,
    SUM(f.revenue_usd) AS total_revenue,
    SUM(f.cost_usd)    AS total_cost,
    ROUND(SUM(f.revenue_usd) / NULLIF(SUM(f.cost_usd), 0), 2) AS roas
FROM fact_ad_events f
JOIN dim_advertiser a ON f.advertiser_key = a.advertiser_key
GROUP BY a.advertiser_name
ORDER BY roas DESC;
```

A ROAS of 1.0 means break-even. A ROAS of 4.0 means the
advertiser earned $4 for every $1 they spent on the
platform. This is the question the advertiser's CFO asks
every Monday.

---

## Tradeoffs to call out

1. **Why one fact, not three?** "The grain is the same
   (one ad, one user, one event). Different facts are
   for different grains. CTR and CVR are ratios over
   the same fact, not joins across facts."
2. **Why 0/1 flag measures instead of separate fact
   tables?** "It keeps the attribution path intact (a
   click is parented to an impression) and makes the
   ratios a CASE WHEN, not a join."
3. **Why denormalize the advertiser hierarchy onto
   the fact?** "Every dashboard joins all five levels.
   The hierarchy is small; the redundancy is one INT
   per row, and the query speed is worth it."
4. **Why is `dim_creative` SCD 1 but `dim_campaign` SCD
   2?** "Creatives are immutable after approval.
   Campaigns change mid-flight (budget, targeting).
   The SCD 2 captures the version that was live on
   each day."
5. **Why a campaign rollup, not a fact table?** "The
   rollup is pre-computed for dashboards. The event
   fact is for deep dives. The analyst doesn't
   `SUM()` billions of rows every time they open a
   dashboard."

---

## Try it

Without looking at the working code, draw the ad-tech
star from memory. Then:

1. State the grain of the fact out loud.
2. Identify which measures are flag columns (0/1) and
   which are financial (REAL).
3. Explain why the advertiser hierarchy is denormalized
   onto the fact.
4. Sketch the campaign rollup table that the ELT job
   would build.

Time yourself: 10 minutes. The full DDL is in
[`code/star_schemas.py`](../code/star_schemas.py) as
`build_online_advertising_schema(q)`. The implementation
is minimal — enough to pass a test, not enough to be
production — but the structure is the same shape you'd
ship to a Google-Ads-style analytics team.

```bash
python3 -m unittest data_modeling/03_high_level_diagrams/tests/test_schemas.py
```

---

## In the interview, you would say...

> "Ad-tech is one event-grain fact, not three — the
> grain is identical (one ad, one user, one event), and
> the headline measures (CTR, CVR, ROAS) are ratios over
> the same scan, not joins across facts. Impressions,
> clicks, and conversions are 0/1 flag columns so
> `SUM(impressions)` and `SUM(clicks)` are cheap. The
> advertiser hierarchy is denormalized onto the fact
> because every dashboard joins all five levels.
> A daily campaign rollup handles dashboards; the event
> fact handles deep dives."

*Author: Prem Vishnoi <prem.vishnoi@example.com>*
