# 93. Snowflake

- **Role:** ML Engineer (Snowpark / Cortex AI)
- **Tech stack:** Python, SQL, Java/Scala, Snowpark, Anaconda, Streamlit, Kubernetes
- **Comp band:** $250K-$700K (L3-L6)
- **Cumulative pass rate:** ~2-3%

## Hiring rounds (5 stages)

| Stage | What happens | Time | Pass rate |
|-------|--------------|------|-----------|
| 1. **Recruiter screen** | Background, team fit (Snowpark, Cortex AI, Search, Marketplace). | 1 week | ~50% advance |
| 2. **Technical phone screen (60 min)** | 1 SQL + 1 coding (Python/Scala) + 1 system design. | 1-2 weeks | ~40% advance |
| 3. **Onsite (4-5 rounds in 1-2 days)** | 2 SQL/coding → 1 system design (data warehouse) → 1 ML (Cortex) → 1 behavioral. | 1-2 days | ~30% advance |
| 4. **Hiring committee** | Packet + calibration. | 1-2 weeks | ~60% advance |
| 5. **Offer** | Comp negotiation. | 1 week | — |

## Stage 1: Recruiter screen (30 min)

### Q1.1: "Tell me about a data pipeline you built at scale."
**Answer:** STAR with scale numbers. Example: "I built a real-time feature pipeline at a fintech, ingesting 50B events/day from Kafka, transforming with Spark, and serving to an online feature store with <100ms p99 latency. The key technical decision: I chose Delta Lake over Iceberg for the ACID guarantees, which reduced data corruption incidents from 1/week to 0."
**Tip:** Snowflake values data engineering depth. Mention specific scale, latency, and the data quality story.

### Q1.2: "Why Snowflake, specifically?"
**Answer:** Specific bet + test + disagreement. "I want to work on the Cortex AI team because the data + AI convergence is the most important architectural shift of 2026. The bet: as models get bigger, the data warehouse becomes the moat — the model is commoditized, the data is the differentiator. The 1 thing I'd test: whether Cortex AI's function-calling interface can match the latency of a custom LLM wrapper at 10K QPS. The 1 thing I disagree with: I think Snowflake is too conservative on the open-source side — open-sourcing the Cortex feature store would accelerate adoption more than the current proprietary path."
**Tip:** Reference Cortex AI + Snowpark + the data cloud thesis.

## Stage 2: Technical phone screen (60 min)

### Q2.1: "Write a SQL query that finds the top 3 most-ordered products in each category, ranked by total revenue, for orders placed in the last 30 days."
**Answer:**
```sql
WITH product_revenue AS (
  SELECT p.category, p.product_id, p.product_name,
         SUM(o.quantity * o.unit_price) AS revenue,
         ROW_NUMBER() OVER (
           PARTITION BY p.category
           ORDER BY SUM(o.quantity * o.unit_price) DESC
         ) AS rn
  FROM orders o
  JOIN products p ON o.product_id = p.product_id
  WHERE o.order_date >= CURRENT_DATE - INTERVAL '30 days'
  GROUP BY p.category, p.product_id, p.product_name
)
SELECT * FROM product_revenue WHERE rn <= 3 ORDER BY category, rn;
```
**Tip:** For Snowflake, mention window functions, CTEs, the use of VARIANT for semi-structured data, and the clustering key optimization for large tables.

### Q2.2: "Implement a sliding-window average over a stream of values. The window is the last N values."
**Answer:**
```python
from collections import deque
class SlidingWindowAvg:
    def __init__(self, n):
        self.n = n
        self.buf = deque()
        self.sum = 0
    def add(self, val):
        self.buf.append(val)
        self.sum += val
        if len(self.buf) > self.n:
            self.sum -= self.buf.popleft()
        return self.sum / len(self.buf)
```
**Tip:** For Snowflake, mention the use of Snowpark Python UDFs, the streaming ingest, and the window functions in SQL.

## Stage 3: Onsite (4-5 rounds)

### Round 3.1: SQL + Coding (60 min, 2 problems)

### Q3.1.1: "Write a SQL query that computes the 7-day rolling retention rate. You have a `login_events(user_id, login_date)` table."
**Answer:**
```sql
WITH day1_users AS (
  SELECT user_id, MIN(login_date) AS d1 FROM login_events GROUP BY user_id
),
day_n AS (
  SELECT d1, login_date, COUNT(DISTINCT le.user_id) AS active
  FROM login_events le JOIN day1_users USING (user_id)
  GROUP BY d1, login_date
),
day1_count AS (SELECT d1, COUNT(*) AS cohort FROM day1_users GROUP BY d1)
SELECT d.d1, d.login_date, d.active / dc.cohort AS retention
FROM day_n d JOIN day1_count dc USING (d1)
WHERE d.login_date BETWEEN d.d1 AND d.d1 + INTERVAL '7 days'
ORDER BY d.d1, d.login_date;
```
**Tip:** For Snowflake, mention QUALIFY for window function filtering, the use of DATE_TRUNC, and the time travel feature for backfilling.

### Q3.1.2: "Implement a feature engineering pipeline that computes lag features (value at t-1, t-7, t-30) and rolling means (7-day, 30-day) for a time-series dataset. Output a pandas DataFrame with the original + new features."
**Answer:**
```python
import pandas as pd
def add_features(df, value_col, date_col):
    df = df.sort_values(date_col)
    g = df.groupby('entity_id')[value_col]
    df['lag_1'] = g.shift(1)
    df['lag_7'] = g.shift(7)
    df['lag_30'] = g.shift(30)
    df['roll_mean_7'] = g.shift(1).rolling(7).mean()
    df['roll_mean_30'] = g.shift(1).rolling(30).mean()
    return df
```
**Tip:** For Snowflake, mention Snowpark pandas API, the use of window functions in SQL (LAG, AVG OVER ROWS), and the importance of avoiding data leakage (always use .shift(1) before .rolling()).

### Round 3.2: System design (60 min, data warehouse)

### Q3.2.1: "Design a data warehouse for a SaaS company. 100K customers, 10B events/day, 5 years of history. Must support ad-hoc SQL queries with <10s p99 latency."
**Answer:** Snowflake-style architecture: (1) storage: columnar, compressed, with micro-partitions. (2) compute: elastic virtual warehouses, auto-suspend on idle. (3) metadata: automatic clustering keys, search optimization. (4) query: vectorized execution, result cache. Trade-off: storage cost vs. query performance. Use the separation of storage and compute.
**Tip:** Mention the micro-partition pruning, the use of clustering keys for large tables, and the separation of storage and compute as the Snowflake differentiator.

### Q3.2.2: "Design a feature store on Snowflake. Discuss online vs. offline, freshness SLA, train/serve skew."
**Answer:** Offline store: Snowflake tables with point-in-time lookups, joined with the entity table. Online store: a low-latency KV store (Redis, DynamoDB) updated via Snowpipe Streaming. Feature definitions in a single Python module imported by both paths to avoid train/serve skew. Trade-off: freshness vs. cost.
**Tip:** Mention Snowflake's Cortex AI feature store, the use of Streams + Tasks for CDC, and the importance of feature versioning.

### Round 3.3: ML deep-dive (60 min, Cortex)

### Q3.3.1: "How would you use Snowflake Cortex to build a RAG system over a corpus of 1M documents? Discuss chunking, embedding, retrieval, and the cost."
**Answer:** (1) chunking: semantic chunking (use Cortex SPLIT_TEXT_RECURSIVE_CHARACTER). (2) embedding: Cortex EMBED_TEXT_768 (Snowflake Arctic embed). (3) storage: store embeddings in a Snowflake table with a vector index (Cortex SEARCH). (4) retrieval: hybrid (BM25 + vector) with Cortex SEARCH_SQL. (5) generation: Cortex COMPLETE with the retrieved chunks in the prompt. Cost: $0.01-0.05 per 1K tokens. Trade-off: recall vs. cost.
**Tip:** Mention the vector index types (IVF, HNSW), the use of metadata filtering, and the importance of eval (RAGAS, LLM-as-judge).

### Q3.3.2: "How would you evaluate a Cortex AI application? What's the offline + online eval framework?"
**Answer:** Offline: held-out test set with a rubric scored by an LLM-as-judge (e.g., GPT-4 class via Cortex COMPLETE). Metrics: faithfulness, relevance, citation accuracy. Online: A/B test on 1% of users, with quality + engagement + safety metrics. Red-team: nightly adversarial queries to catch regressions.
**Tip:** Mention the use of Snowflake's eval harness (Cortex EVALUATE), the importance of production monitoring, and the LLM-as-judge calibration against human labels.

### Round 3.4: Behavioral (45 min)

### Q3.4.1: "Tell me about a time you had to optimize a slow SQL query. What was the bottleneck, and what did you do?"
**Answer:** Use STAR. Situation (the query, the table size, the original latency), Task (your role), Action (EXPLAIN, identify the bottleneck — full table scan, missing index, bad join order), Result (new query plan, new latency, cost reduction). Example: "I reduced a 10-minute query to 30 seconds by adding a clustering key on the date column, which enabled micro-partition pruning."
**Tip:** Snowflake values SQL optimization. Mention specific commands (EXPLAIN, SHOW TABLES, clustering depth), the use of query history, and the warehouse sizing.

## Stage 4: Hiring committee
The committee reviews the packet and votes. Snowflake has a calibration committee to ensure consistency across teams. ~60% advance.

## Stage 5: Offer
Cash + RSU comp. Comp band L3-L6: $250K-$700K. Snowflake comp is RSU-heavy (4-year vest, 1-year cliff). Comp negotiation is real at L4+.

## Tips for the Snowflake loop

1. **SQL is non-negotiable.** Window functions, CTEs, query optimization, micro-partitions. Do 30 SQL mediums.
2. **The data warehouse domain is the signal.** Columnar storage, separation of storage and compute, clustering keys.
3. **Cortex AI is the 2026 differentiator.** RAG, embeddings, feature store, LLM-as-judge. Read the Cortex docs.
4. **Snowpark is the Python API.** Pandas-style DataFrames, UDFs, the streaming ingest.
5. **System design is always data-warehouse themed.** Feature store, RAG pipeline, real-time ingestion, query optimization.

## Real candidate report

> "Snowflake's loop is the most data-engineering-focused of the cloud data warehouse companies. The SQL round tested window functions, CTEs, and query optimization. The system design was a feature store + RAG pipeline on Snowflake. The ML round was Cortex AI: chunking, embedding, retrieval, eval. If you've worked on a data warehouse, this is the best-fit company in the space."
> — r/dataengineering, on the Snowflake loop

## Sources

- [Levels.fyi — Snowflake compensation](https://www.levels.fyi/companies/snowflake/salaries/software-engineer)
- [Snowflake Engineering Blog](https://www.snowflake.com/blog/) — the data cloud architecture posts
- [Snowflake Cortex AI docs](https://docs.snowflake.com/en/user-guide/snowflake-cortex/llm-functions) — the RAG + LLM functions
- [Snowpark docs](https://docs.snowflake.com/en/developer-guide/snowpark/index) — the Python API
- [r/dataengineering — Snowflake interview threads](https://www.reddit.com/r/dataEngineering/)
