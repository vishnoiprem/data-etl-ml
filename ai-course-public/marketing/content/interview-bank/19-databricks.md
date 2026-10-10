# 19. Databricks (Mosaic AI)

- **Role:** ML Engineer
- **Tech stack:** Python, PySpark, SQL, MLflow, Delta Lake, Unity Catalog
- **Comp band:** $180K-$1.4M+ (L3-L7)
- **Cumulative pass rate:** ~2-3%

## Hiring rounds

| Stage | What happens | Time | Pass rate |
|-------|--------------|------|-----------|
| 1. **Recruiter screen** | Background, team fit (ML Platform, Data Eng, Mosaic AI) | 1 week | ~50% advance |
| 2. **Technical coding screen (60 min)** | LeetCode medium + SQL + ML implementation | 1-2 weeks | ~40% advance |
| 3. **Virtual onsite (4-5 rounds in 1-2 days)** | 2 coding → 1 system design (ML platform) → 1 ML deep-dive → 1 behavioral | 1-2 days | ~30% advance |
| 4. **Hiring committee** | Packet → committee vote | 1 week | ~60% advance |
| 5. **Team match + offer** | Match to a team | 1 week | — |

## Stage 1: Recruiter screen (30 min)

### Q1.1: "Tell me about your background"
**Answer:** I'm an ML engineer with 5 years in production ML — most recently at [X] where I built a feature store on Delta Lake that served 1B features/day. Relevant: a Bronze-Silver-Gold pipeline for a recommendation system that scaled to 100TB. I'm targeting Databricks Mosaic AI because the data + AI convergence is the most important architectural shift of 2026.
**Tip:** Databricks grades Spark + ML platform depth; bring Delta Lake + MLflow specifics.

### Q1.2: "Why Databricks?"
**Answer:** I want to work on Mosaic AI because as models get bigger, the data layer becomes the moat — the model is commoditized, the data is the differentiator. The 1 thing I'd test: whether Mosaic AI Model Serving hits <50ms p99 for a 7B model at 10K QPS. The 1 thing I disagree with: Databricks should be more aggressive on the open-source side.
**Tip:** Specific product + specific bet + specific test + specific disagreement.

## Stage 2: Technical coding screen (60 min)

### Q2.1: "Implement a windowed aggregation in PySpark with late-arriving data"
**Answer:**
```python
from pyspark.sql import SparkSession
from pyspark.sql.functions import window, col
spark = SparkSession.builder.getOrCreate()
events = spark.readStream.format("kafka")...
agg = events.withWatermark("event_time", "10 minutes") \
    .groupBy(window(col("event_time"), "5 minutes"), col("user_id")) \
    .count()
query = agg.writeStream.outputMode("append").start()
```
Watermarking handles late-arriving data: the watermark is the max event time seen minus the threshold; events older than the watermark are dropped. `groupBy(window(...))` is a tumbling window.
**Tip:** Watermarking is the Databricks-canonical answer for late data.

### Q2.2: "Second-highest salary per department, with and without window functions"
**Answer:**
```sql
-- Without window:
SELECT MAX(salary) FROM emp WHERE salary < (SELECT MAX(salary) FROM emp);
-- With window:
SELECT salary FROM (SELECT salary, DENSE_RANK() OVER (PARTITION BY dept ORDER BY salary DESC) rk FROM emp) WHERE rk=2;
```

## Stage 3: Virtual onsite (4-5 rounds)

### Round 3.1: Coding (systems-flavor)

### Q3.1.1: "Top-K most frequent items in a sliding window"
**Answer:** Count-min sketch for approximate frequency; min-heap of size K for the top-K. For exact: hash map + heap, O(n log K). For distributed: Spark windowed aggregation with `array_sort` + `slice`.

### Q3.1.2: "Event-time join between two streams with out-of-order events"
**Answer:** Both streams watermarked; state stored in a stateful operator keyed by join key; rows buffered until the watermark passes. Trade-off: state size vs. latency. Higher watermark = more buffering but fewer late drops.

### Round 3.2: ML implementation (60-90 min)

### Q3.2.1: "Implement K-Means in PySpark RDD API"
**Answer:** `data.map(lambda x: (closest_centroid(x, centroids), x)).reduceByKey(lambda a,b: (a[0]+b[0], a[1]+b[1])).mapValues(lambda v: v[0]/v[1])` → new centroids. Iterate. Shuffle cost: `reduceByKey` is map-side combined; `groupByKey` is the wrong pick for high-cardinality keys (data skew).
**Tip:** Name the DAG, name the shuffle cost, name the data skew.

### Q3.2.2: "ALS recommendation system, cold-start + implicit feedback"
**Answer:** ALS minimizes ||R - PQᵀ||² + λ(||P||² + ||Q||²). Cold-start: fall back to item-item similarity or content features for new users/items. Implicit feedback (clicks, views): treat confidence as 1 + α·count, minimize the same objective with weights.
**Tip:** Name the loss, the cold-start fallback, the implicit-feedback variant.

### Round 3.3: System design (ML platform, 60 min)

### Q3.3.1: "Design a feature store"
**Answer:** Online (low-latency, <10ms, real-time inference) + offline (high-throughput, batch training). Online: Redis/DynamoDB with freshness SLA <1 min. Offline: Delta Lake with feature definitions in Unity Catalog. Consistency: offline is source of truth; online is a derived view via CDC. Train/serve skew: feature definitions in a single Python module imported by both paths.
**Tip:** Name the online/offline split, the freshness SLA, the train/serve skew fix.

### Q3.3.2: "Design a training data pipeline: Bronze-Silver-Gold"
**Answer:** Bronze: raw, append-only, schema-on-read, lands in Delta Lake. Silver: cleaned, deduplicated, conformed to a canonical schema, PII tokens. Gold: aggregated, business-level features, materialized for ML training. The bet: decoupling ingestion from transformation means a schema change in the upstream source doesn't break the ML pipeline.
**Tip:** Name the 3 layers, the trade-off, the reproducibility win.

### Round 3.4: Behavioral (45 min, Leadership Principles-style)

### Q3.4.1: "A time you debugged a production Spark job on 10TB"
**Answer:** A job was failing with OOM at the shuffle stage. I checked the Spark UI: 1 task reading 200GB. Root cause: data skew — a single key had 50M rows. Fix: salting (add a random prefix to the key for the shuffle), then secondary aggregation. OOM gone; runtime dropped 4×.
**Tip:** Specific bug, specific root cause, specific fix, specific metric.

### Q3.4.2: "A time you had to ship a complex data pipeline under a tight deadline"
**Answer:** 2 weeks to ship a customer-facing analytics pipeline. I cut: the validation suite (kept only the 50 most-critical checks), the monitoring alerts (deferred to v2), the documentation (replaced with a 1-page README). Quality held; velocity worked.
**Tip:** Name what you cut, why, and what held.

## Stage 4: Hiring committee

The committee weighs Spark internals + ML platform depth + Mosaic AI bet. They look for: (1) coherent data + AI narrative, (2) Bronze-Silver-Gold fluency, (3) MLflow + Unity Catalog knowledge, (4) "would I want to ship to a customer with this person?" 1-week turnaround is normal.

## Stage 5: Offer

Databricks comp is base + RSU + sign-on. Total $180K-$1.4M+ L3-L7. The play: anchor with a competing offer (Snowflake, Microsoft, Google). RSUs vest 4 years. Sign-on is real for senior candidates.

## Tips for the Databricks loop

- **Spark internals are non-negotiable.** Catalyst, Tungsten, lazy eval, DAG. 8 hours on Spark.
- **Medallion architecture is the 2026 emphasis.** Bronze-Silver-Gold, Delta Lake, Unity Catalog.
- **MLflow + Unity Catalog are the platform tools.** Every ML question uses them.
- **System design is ML-platform-themed.** Feature store, model serving, training data.
- **SQL + Python, not heavy Java.** Databricks uses PySpark and SQL.
- **"Why Databricks" needs a specific product.** Mosaic AI, MLflow, Delta Lake.
- **Watermarking is the late-data answer.** Name the threshold, the state, the trade-off.

## Real candidate report

> *"For ML Engineer roles, expect a mix of algorithmic problems and statistics or ML implementation questions. Databricks is unique in that the coding questions often have a 'systems' flavor — they test whether you can write a windowed aggregation, an event-time join, or a streaming pipeline that handles late-arriving data."*
> — [AIOfferly — Databricks ML Interview Questions (2026)](https://www.aiofferly.com/career-guide/databricks-ml-interview-questions)

## Sources

- [AIOfferly — Databricks ML Interview Questions (2026)](https://www.aiofferly.com/career-guide/databricks-ml-interview-questions)
- [DataCamp — Top Databricks Interview Questions and Answers for 2026](https://www.datacamp.com/blog/databricks-interview-questions)
- [Final Round AI — Databricks Interview Process: Complete 2026 Guide](https://www.finalroundai.com/blog/databricks-interview-process)
- [Databricks — Interview Prep (Official)](https://www.databricks.com/company/careers/interview-prep)
- [Levels.fyi — Databricks compensation](https://www.levels.fyi/companies/databricks/salaries/software-engineer)