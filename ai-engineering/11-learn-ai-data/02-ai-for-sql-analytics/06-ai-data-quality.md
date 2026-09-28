# Lesson 6 — AI Data Quality

> **Type:** Article · Module 2 · AI for SQL & Analytics
> Drift, anomaly detection, freshness monitoring, and where AI-driven data quality beats hand-written assertions.

---

## The gap AI data quality fills

Hand-written assertions catch **what you expect to break**. AI anomaly detection catches **what you didn't expect to break**.

```
   ┌──────────────────────────────────────────────────────────┐
   │  WHAT EACH CATCHES                                        │
   │                                                          │
   │   Hand-written assertions (dbt tests, Great Expectations) │
   │   ✅ NULL in PK                                           │
   │   ✅ Duplicate PK                                         │
   │   ✅ Negative amount                                      │
   │   ✅ Value outside enumerated list                        │
   │   ❌ "Average order value silently dropped 14% on Tuesday"│
   │   ❌ "Volume 3x normal because of upstream double-count" │
   │   ❌ "Schema added a new column you didn't know about"   │
   │                                                          │
   │   AI-driven anomaly detection                            │
   │   ✅ All of the above (with hand-written rules layered)   │
   │   ✅ Distribution drift                                   │
   │   ✅ Cardinality anomalies                                │
   │   ✅ Freshness issues                                     │
   │   ✅ Schema drift                                         │
   └──────────────────────────────────────────────────────────┘
```

The two together cover **the assertions you know to write** and **the assertions you didn't know you needed**.

---

## The four pillars

### 1. Freshness
*"Is the data arriving on time?"*

```sql
-- hand-written
SELECT MAX(loaded_at) FROM {table};
-- alert if older than SLA
```

AI-driven: learns the loading pattern per table per day-of-week, alerts on deviation.

### 2. Volume
*"Is the row count what we expect?"*

```sql
-- hand-written: row count between [lower, upper]
```

AI-driven: learns the daily distribution, alerts on >N stddev deviation.

### 3. Schema
*"Did the schema change?"*

Hand-written: brittle, only catches known columns.
AI-driven: detects new columns, type changes, dropped columns.

### 4. Distribution
*"Did the *shape* of the data change?"*

This is where AI shines. No human writes "average order value is between $X and $Y" because nobody knows the right bounds. AI learns them.

---

## The vendor landscape

| Vendor | Approach | Strength |
|---|---|---|
| **Monte Carlo** | ML-driven, end-to-end | Strongest out-of-the-box |
| **Anomalo** | ML-driven, no-code | Easy rollout |
| **Datadog (Metaplane)** | Observability-integrated | Best if you're already on Datadog |
| **Bigeye** | ML + rule-based | Good for warehouse-centric teams |
| **Great Expectations + AI** | Open-source + add-ons | Best for OSS-first shops |
| **dbt tests + Soda** | Rule-based with AI assist | Good if you're already on dbt |

---

## The architecture

```
   ┌──────────────┐
   │  Sources     │  Kafka, S3, APIs
   └──────┬───────┘
          │
          ▼
   ┌──────────────┐
   │  Ingestion   │  Airflow / dbt / Flink
   └──────┬───────┘
          │
          ▼
   ┌──────────────┐     ┌──────────────────┐
   │  Warehouse   │────►│  AI DQ Engine    │
   │  (Snowflake/ │     │  (Monte Carlo /  │
   │   BigQuery/  │     │   Anomalo / etc) │
   │   Databricks)│     └────────┬─────────┘
   └──────────────┘              │
                                 ▼
                       ┌──────────────────┐
                       │  Alerting        │  Slack / PagerDuty / Email
                       │  + incident log  │
                       └──────────────────┘
                                 │
                                 ▼
                       ┌──────────────────┐
                       │  Hand-written    │  dbt tests, GE, Soda
                       │  assertions      │  layered on top
                       └──────────────────┘
```

The AI DQ engine sits **on top of** the warehouse, watching every table. Hand-written assertions live in the dbt project, close to the code.

---

## The hand-written + AI hybrid pattern

| Layer | Catches | Examples |
|---|---|---|
| **dbt tests** | Known invariants | not_null, unique, accepted_values, relationships |
| **Soda / Great Expectations** | Domain rules | "revenue per order > 0", "every customer has a country" |
| **AI anomaly detection** | Unknown unknowns | "average order value drifted 14%", "cardinality on status column dropped" |

You don't pick one. You layer them.

---

## Prompt — write dbt tests from a table

```text
ROLE: senior analytics engineer at {COMPANY}.

TASK: Given the following table, generate dbt tests for the schema.yml.

TABLE: {TABLE}
COLUMNS:
- {col1} ({type}, {nullable}, {description})
- {col2} ...
- {PK} is the primary key
- {FK} joins to {OTHER}

GENERATE:
1. not_null + unique on the PK
2. relationships test on each FK
3. accepted_values on {low-cardinality columns}
4. expression_is_true tests on {obvious business rules}
5. dbt_utils.expression_is_true on {numerical columns with obvious bounds}

FORMAT: YAML in a ```yaml block, ready to drop into schema.yml.

CONSTRAINTS:
- Don't over-test. 5-10 tests is right for most tables.
- Don't test things AI anomaly detection catches (distribution drift).
```

This produces a solid first cut in 30 seconds. You review and ship.

---

## The freshness SLO pattern

```yaml
# freshness.yml (dbt source-level)
sources:
  - name: stripe
    loaded_at_field: _loaded_at
    freshness:
      warn_after: { count: 6, period: hour }
      error_after: { count: 12, period: hour }
```

AI-driven engines learn the pattern per source per day-of-week. Tuesday at 03:00, a 2-hour delay is normal. Tuesday at 14:00, it's not.

---

## The "what to alert on" checklist

Before alerting, answer:

- [ ] Is this **actionable**? (Can someone fix it?)
- [ ] Is this **novel**? (Has it happened before? If yes, is it a regression?)
- [ ] Is this **impactful**? (Does it affect a downstream dashboard / decision?)
- [ ] Is the **severity** correct? (page / slack / dashboard?)

If "no" to any of these, downgrade the alert. Alert fatigue is worse than missed alerts.

---

## The "where AI DQ fails" honesty

- **Spike vs. seasonality**: Black Friday volume spikes. AI has to learn "expected" seasonally.
- **One-off backfills**: a 10× row-count jump is a backfill, not a bug.
- **New tables**: no training data yet.
- **Concept drift that's intentional**: business changes, AI flags it as drift.

You need a way to **mark expected anomalies** ("this is a known event, don't alert"). Without it, you turn off the alerts in 2 weeks.

---

## What Comes Next

> Lesson 7 — **Quiz: AI for SQL & Analytics** — self-check on the seven lessons of Module 2.
