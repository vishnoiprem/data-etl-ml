# Lesson 4 — Data Exploration & Profiling

> **Type:** Article · Module 2 · AI for SQL & Analytics
> Using AI to accelerate the first 30 minutes with a new dataset.

---

## Why exploration matters

The first 30 minutes with a new dataset decide whether the next 30 days go well or badly. AI compresses that first 30 minutes from 2 hours to 15 — **if you use it correctly**.

The pattern is **structured exploration**: schema → distribution → relationships → anomalies → first questions.

```
   ┌────────────────────────────────────────────────────────┐
   │  STRUCTURED EXPLORATION IN 15 MINUTES                  │
   │                                                        │
   │   0:00  Schema + row count + freshness                 │
   │   0:02  Column types + nulls                           │
   │   0:05  Distribution of numeric columns                 │
   │   0:08  Cardinality of categorical columns             │
   │  0:10  Time-series shape + gaps                         │
   │  0:12  Relationships (joins)                            │
   │  0:15  Anomalies / drift                                │
   │                                                        │
   │  → first 5 questions answered                          │
   │  → first 10 hypotheses formed                          │
   │  → you know what you don't know                        │
   └────────────────────────────────────────────────────────┘
```

---

## The exploration prompt sequence

### Step 1 — schema

```text
For the table {SCHEMA}.{TABLE}:
1. List every column with type and nullability.
2. Identify the most likely primary key.
3. Identify the most likely foreign keys (by name pattern).
4. Estimate row count and physical size.
5. Note any obviously suspicious columns (free text, JSON, very wide).
```

### Step 2 — column profiles

```text
For each column in {TABLE}, return:
- null rate (%)
- distinct count + sample of 5 values
- for numerics: min, max, mean, stddev, p50, p95, p99
- for timestamps: min, max, recent activity
- for strings: avg length, max length, sample
```

### Step 3 — relationships

```text
For {TABLE}, identify likely join candidates to:
- {OTHER_TABLE_1}
- {OTHER_TABLE_2}

For each, give the candidate key, expected cardinality (1:1, 1:many, many:many),
and the matching-rate I'd see in a LEFT JOIN.
```

### Step 4 — anomalies

```text
For {TABLE}, generate queries that detect:
- rows with NULL in any column that "should not" be NULL
- duplicate primary keys
- values outside expected range (negative quantities, future dates)
- cardinality anomalies (a category appearing 10x more than expected)
- sudden volume or distribution shifts in the last 7 days
```

### Step 5 — first business questions

```text
Given everything above, suggest the 5 most likely business questions
someone would ask of this table, with example SQL for each.
```

---

## AI profiling tools

For local CSVs / Parquet:

```python
import pandas as pd
import pandas_profiling  # or ydata-profiling

df = pd.read_parquet("data.parquet")
profile = pandas_profiling.ProfileReport(df)
profile.to_file("profile.html")
```

AI tools add the "explain what I see" layer:

- **PandasAI** — query the dataframe with English
- **Hex AI** — notebook cells with AI suggestions
- **Deepnote AI** — same, deeper integration
- **Databricks Assistant** — `/cmd` commands in notebooks

For warehouse data:

- **Snowflake Cortex** — `SNOWFLAKE.CORTEX.SUMMARIZE`, classification, sentiment
- **BigQuery Gemini** — natural-language SQL + insights
- **Databricks AI Functions** — `ai_classify`, `ai_extract`, `ai_summarize` in SQL

---

## The "explain the column" prompt

```text
ROLE: senior analytics engineer at {COMPANY}.

CONTEXT: I'm looking at {TABLE}.{COLUMN}. Values look like: {SAMPLE}.

TASK:
1. What does this column likely represent?
2. What's the business context (what process generates this)?
3. What would I need to confirm with the data owner?
4. Are there any red flags in the values?
5. Is this PII? If so, what's the safe handling?
```

The answer is rarely 100% right. The answer is **faster than starting from scratch**.

---

## The distribution shape test

A column's distribution tells you **what kind of model to use** and **what kind of joins to expect**.

```sql
-- basic distribution
SELECT
  percentile_cont(0.01) WITHIN GROUP (ORDER BY amount) AS p01,
  percentile_cont(0.50) WITHIN GROUP (ORDER BY amount) AS p50,
  percentile_cont(0.95) WITHIN GROUP (ORDER BY amount) AS p95,
  percentile_cont(0.99) WITHIN GROUP (ORDER BY amount) AS p99,
  MAX(amount), MIN(amount), AVG(amount), STDDEV(amount)
FROM fct_orders;
```

AI can interpret these and tell you: *"heavy-tailed, consider log-transform; p99 is 100× median — likely fraud or enterprise tier."* Useful framing you wouldn't get from raw numbers.

---

## The exploration deliverable

After 15 minutes, write a 1-page dataset card:

```markdown
# Dataset card — fct_orders

## What
- One row per order. PK: order_id.
- Updated daily at 03:00 UTC. 50M rows, ~2 GB.

## Columns
- order_id (varchar): PK
- user_id (varchar): FK to dim_user, ~3% NULL (guest checkout)
- gross_amount (numeric): USD cents, [0, 1e7], p99 = $850
- status (varchar): 6 values, dominated by 'fulfilled' (78%)
- created_at (timestamp_ntz): UTC, indexed
- ...

## Relationships
- fct_orders.user_id = dim_user.user_id (LEFT JOIN, ~3% orphan)
- fct_orders.order_id = fct_order_items.order_id (1:many)

## Anomalies
- ~0.1% rows have status='cancelled' but refunded_amount IS NULL
- user_id has 0.4% distinct string IDs that look like test accounts (user_xxxxx)

## Don't know
- the exact revenue recognition rule (ask Finance)
- the SLA for freshness (ask the pipeline owner)
```

This is the artifact you hand to the next person. AI helps write it; you sign off.

---

## What Comes Next

> Lesson 5 — **NL Analytics Interfaces** — building a "ChatGPT for our data" that actually works. The semantic layer, the eval harness, and the failure modes that kill the project.
