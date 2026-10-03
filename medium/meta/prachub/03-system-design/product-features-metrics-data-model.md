# Define Metrics and Data Model for Product Features

## 1. Simple way to think

- Imagine you just shipped a new "Save to Collection" button on Instagram. Leadership asks: is it working? You need three things: a number (the metric), a chart (the dashboard), and a way to compute the number from raw data (the data model).
- The metric isn't just "people who saved stuff." That's vanity. The right metric is something tied to a **business goal**: are saves leading to more time spent, more sessions, more creation? That's the **metric hierarchy**.
- The hierarchy: **North Star Metric** (one number that captures product health, e.g. "time well spent"), then **driver metrics** (the levers that move it), then **operational metrics** (the day-to-day stuff PMs track).
- The dashboard should answer four questions: Are we growing? Are users engaged? Are they retained? Are we monetizing? Pick one chart per question. Don't make a 50-tile dashboard nobody reads.
- The data model needs to support the dashboard *and* allow drill-down. If a metric says "engagement is down 5%," you need to slice it by country, age, platform to find the cause.
- A common mistake is **denominator confusion**. "Saves per user" — per what? Per day, per week, per active user, per session? Pick the denominator carefully or every chart lies.
- Another mistake: **lumping rare and common events**. "Power users" and "casual users" have different behaviors. The averages hide this. Always segment.
- Concrete example: a "Stories" feature. North Star: time well spent. Driver: Stories viewed per day. Operational: completion rate, share rate, swipe-away rate. Data model: events table joined to user dimension and experiment assignment.

## 2. Interview write-up (how to solve it)

**Requirements clarification.** "Before I propose metrics, which feature are we measuring, and what's the business goal — growth, engagement, monetization, or all three? I'll use a concrete example: a new 'Close Friends Stories' feature on Instagram."

**Step 1: Define the goal.** Close Friends Stories is a private sharing surface. Business goals: (a) drive daily engagement, (b) strengthen creator-user connection, (c) increase time-spent without annoying the casual viewer.

**Step 2: Build the metric pyramid.**

```
                  [North Star]
              Time Well Spent (min/user/day)
                       ▲
                       │
       ┌───────────────┼───────────────┐
       │               │               │
  [Reach: DAU]   [Engagement:    [Depth: Saves/
                Stories viewed/   Shares per
                  session]        viewer]
       ▲               ▲               ▲
       │               │               │
  Operational:    Operational:    Operational:
  - New users    - Completion     - Saves → 
  - 7-day        - Swipe-away       revisit
    retention    - Reply rate     - Share → 
  - Notification                   virality
    opt-in
```

**Step 3: Specific metrics and definitions.**

| Metric | Definition | Why |
|--------|-----------|-----|
| DAU | Unique users opening app on a given day | Reach baseline |
| Daily Stories Viewed / User | `sum(story_impressions) / DAU` | Engagement breadth |
| Story Completion Rate | `completed_views / started_views` | Content quality |
| Saves per Active User | `sum(save_events) / DAU` | Depth signal |
| 7-Day Retention | Users active on day 7 ÷ cohort size | Stickiness |
| Close Friends DAU | Users who posted/viewed CF in last 7 days | Feature-specific reach |
| CF Share Rate | `cf_share_events / cf_story_impressions` | Virality |

**Step 4: Dashboard design.**

```
┌────────────────────────────────────────────────────┐
│  [Headline: Time Well Spent]    Δ +3.2% vs last wk │
├────────────┬────────────┬────────────┬─────────────┤
│   DAU      │ Stories/   │ Completion │ 7-day Ret.  │
│  312M ▲2%  │ User 14.2  │  68% ▲1pt  │  45% flat   │
├────────────┴────────────┴────────────┴─────────────┤
│  Time-series: Time Well Spent by cohort (last 90d) │
│  ────────────────────╱──╲___╱──╲___                 │
├────────────────────────────────────────────────────┤
│  Funnel: View → Complete → Reply → Save → Share   │
│  ████████████ 100%                                    │
│   ████████ 68%                                       │
│    ███ 18%                                            │
│     █ 9%                                              │
│      █ 4%                                             │
├────────────────────────────────────────────────────┤
│  Segmentation heatmap: country × age × platform    │
│  (color = engagement lift vs. baseline)            │
└────────────────────────────────────────────────────┘
```

**Step 5: Data model.**

```sql
-- Daily aggregate (the "metric mart")
CREATE TABLE metrics_daily (
  date_key        INT,        -- YYYYMMDD
  feature         VARCHAR(32),  -- 'cf_stories', 'feed', 'reels'
  cohort          VARCHAR(64),  -- e.g. 'US_18-24_ios'
  dau             BIGINT,
  total_events    BIGINT,
  unique_actors   BIGINT,
  completion_rate DECIMAL(5,4),
  -- pre-computed for dashboard speed
  PRIMARY KEY (date_key, feature, cohort)
) PARTITION BY RANGE (date_key);

-- User-level rollup for drill-down
CREATE TABLE user_feature_metrics_daily (
  user_id         BIGINT,
  date_key        INT,
  feature         VARCHAR(32),
  events          INT,
  sessions_with_feature INT,
  last_event_at   TIMESTAMPTZ,
  PRIMARY KEY (user_id, date_key, feature)
) PARTITION BY RANGE (date_key);

-- Source-of-truth events
-- events_raw (defined in event analytics question)
-- with feature='cf_stories' events: impression, view, complete, reply, save, share
```

**Step 6: Pipeline.**

```
[Client SDK] -> Kafka -> Flink (bot filter, dedup)
                              │
                              ├──> events_raw (Iceberg, partitioned by date)
                              │
                              └──> Airflow daily 2am:
                                    1. Aggregate events → user_feature_metrics_daily
                                    2. Roll up to cohort level → metrics_daily
                                    3. Compute deltas vs. baseline
                                    4. Publish to dashboard DB
```

**Trade-offs.**
- Pre-aggregated `metrics_daily` is fast but stale up to 24h. Real-time variant adds cost.
- Cohort segmentation explodes cardinality — limit to ~50 standard cohorts.
- Funnel order matters: hardcode based on product flow, don't derive dynamically.

**Failure modes.** Tracking plan gaps: missing events show as 0 in funnel. Bot inflation: filter before aggregation. Timezone: DAU in UTC vs. local time can shift numbers by 5%. Backfill: when schema changes, every downstream metric needs re-computation — version your metrics.

## 3. Best optimized solution

**Refined metric platform.**

```
[Client events] ──> Kafka ──> Flink ──> Iceberg (raw)
                                          │
                              ┌───────────┼────────────┐
                              v           v            v
                    user_feature_    session_     metrics_daily
                    metrics_daily    metrics      (cohort-level)
                              │           │            │
                              └───────────┼────────────┘
                                          v
                                  [Semantic Layer]
                                  (dbt models with versioned
                                   metric definitions)
                                          │
                              ┌───────────┼────────────┐
                              v           v            v
                          Tableau     ML features   Anomaly alerts
```

**Semantic layer.** Metrics defined in code (dbt / LookML), version-controlled, with single source of truth. `time_well_spent` is defined once; every dashboard uses the same definition. Prevents "two teams report different DAU" embarrassment.

**Storage choices.**
- Raw events: Iceberg/Parquet, ZSTD, partitioned by date.
- `user_feature_metrics_daily`: columnar Parquet, clustered by `feature, user_id`.
- `metrics_daily`: small (millions of rows), Parquet, clustered by `date_key, feature`.

**Cost & freshness.** Daily rollup runs at 2am, completes by 3am, dashboard reads from 3am onwards. Cost is negligible because pre-aggregation is the whole point. Live dashboards (executive view) read from a Flink-maintained 5-minute aggregate.

**Anomaly detection.** A daily job compares each metric against the prior 28-day forecast (Prophet or simple z-score). Alerts via PagerDuty if any North Star or driver metric moves > 3 standard deviations. Avoids the "nobody noticed engagement dropped 8%" problem.

**SLOs.**
- Dashboard freshness: < 4 hours after midnight UTC.
- Metric accuracy: < 0.1% drift between dashboard and source-of-truth.
- Coverage: 100% of released features have metrics defined before launch (gated by release pipeline).

**Why it's optimal.**
- The metric pyramid stops teams from optimizing the wrong thing — every chart traces back to the North Star.
- Pre-aggregation in `metrics_daily` makes dashboards load in <2s and queries cheap. The drill-down path to `user_feature_metrics_daily` is one click away.
- A semantic layer in dbt prevents the #1 data team failure mode: two definitions of the same metric.
- Anomaly detection turns dashboards from "I have to remember to check" into "the dashboard tells me when something's wrong."

**What the interviewer is really testing:** They want product sense *and* data engineering competence in one answer. Can you pick a North Star that's not vanity? Can you build a metric hierarchy where each level rolls up cleanly? Can you design a dashboard that PMs and execs would actually use? Can you build a data model that supports both the headline number and drill-down? Meta looks for people who think in systems: a metric isn't a number in a spreadsheet, it's a definition in code, a pipeline that computes it, a dashboard that surfaces it, and an alert when it breaks. Bonus: do you think about the *first time* a new feature needs metrics, and do you instrument it *before* launch, not after?
