# Technical Accuracy Audit — Katalon Interview Prototypes

**Auditor:** Senior data engineer (production PySpark / Delta Lake / Databricks)
**Subject:** 5 code prototypes (A–E) for Head of Data interview prep
**Verdict:** Conceptually correct. Need hardening on partition pruning, type safety, tenant binding, hash selection, and outbox atomicity before any survive a 30k-tenant production load.

## How to read this

The audit splits findings into three severities because they require different responses:

- **BUG** is a correctness failure — the code does not do what the docstring claims, or returns a wrong answer in some input. These must be fixed before the demo runs in front of the panel; the panel will catch them.
- **RISK** is something the code gets away with at demo scale (12 rows, 1 tenant, `local[2]`) but breaks at 30k-tenant production scale. These don't change the demo, but if you don't acknowledge them out loud, the panel will assume you don't see them.
- **FIX** is the corrected code. Read the FIX section before re-running the prototype.

The prototypes are *interview demos*, not production code. The point of the audit isn't to ship them — it's to make sure you can stand behind them under cross-examination. Saying "this is a demo; in production I'd swap parquet for Delta with merge, partition by tenant, and use a content hash for idempotency" is stronger than showing a demo that *happens* to use parquet. The first demonstrates judgment. The second demonstrates unfamiliarity with Delta.

The single most important sentence in this audit: **the demo runs on `local[2]` with 12 rows. The interview is about what you'd build for 30k tenants. The audit is the bridge between the two.**

---

## Prototype A — CDC Dedup to Silver (Idempotent Merge)

**What it proves:** Re-running a write produces the same row count, validating dedup stability across replays.

### PASS
- Correct dedup key: `(tenant_id, execution_id, test_case_id, attempt_id)` is the natural grain.
- Tie-breaker `aggregate_version DESC → ingested_at DESC → source_offset DESC` is defensible.
- `row_number().over(window)` is the right primitive for "latest record wins."

### BUG
1. **`monotonically_increasing_id()` is NOT stable across query re-executions.** Depends on partition ID + offset. Two calls in the same plan can collide. Real bug: when you `UNION ALL` `cdc_raw` with itself, MII in each branch restarts at 0 per partition — the two copies of the same row get different offsets per branch, which accidentally helps here but is fragile. Don't rely on MII for ordering.
2. **`ingested_at` is a string, not a timestamp.** `orderBy(ingested_at)` will lexicographically sort — works for ISO 8601 but breaks for `"2026-9-1 10:00:5"`. Cast upstream.
3. **`write_silver()` not idempotent across "process" restarts** because of `tempfile.mkdtemp()`. In production this would be a Delta path like `s3://bucket/silver/test_results`.
4. **No `tenant_id` predicate / schema enforcement.** A missing `tenant_id` column on the silver path silently produces nulls.
5. **No schema evolution handling.** Plain `parquet` writes without `mergeSchema`. Adding a column downstream silently drops old partitions on read.
6. **`attempt_id` is treated as opaque ordering input.** The window partition does not include `attempt_id` ordering — fine, but the intent suggests otherwise.

### RISK
- **`spark.sql.shuffle.partitions=2`** — at 30k tenants this creates catastrophic shuffle. Use 200+ in prod.
- **Local mode `[2]`** masks serialization issues. PySpark UDFs on `test_case_id` would silently fail or OOM in prod.
- **`setLogLevel("ERROR")`** hides OOM/skew warnings during development.
- **Window without partition pruning**: source scan reads ALL tenants before filtering. Real pipeline partitioned by `tenant_id` and date.
- **The "second write produces same count" check is weak** — validates row count, not row content.

### FIX

```python
import hashlib
from delta.tables import DeltaTable

# Fix 1: stable tiebreaker that doesn't depend on MII
df_dedup = (spark.table("cdc_raw")
    .withColumn("ingested_at_ts", F.to_timestamp("ingested_at"))
    .withColumn("dedup_key",
        F.concat_ws("|", "tenant_id","execution_id","test_case_id","attempt_id"))
    .withColumn("content_hash",
        F.sha2(F.concat_ws("||",
            "tenant_id","execution_id","test_case_id","attempt_id",
            "status","aggregate_version",
            F.col("ingested_at_ts").cast("string")), 256))
    .withColumn("rn",
        F.row_number().over(
            Window.partitionBy("dedup_key")
                  .orderBy(F.col("aggregate_version").desc(),
                           F.col("ingested_at_ts").desc(),
                           F.col("content_hash"))))
    .filter("rn = 1").drop("rn"))

# Fix 2: idempotent Delta merge, not parquet overwrite
silver_path = "s3://katalon-silver/test_results"
if DeltaTable.isDeltaTable(spark, silver_path):
    tgt = DeltaTable.forPath(spark, silver_path)
    (tgt.alias("t").merge(df_dedup.alias("s"), "t.dedup_key = s.dedup_key")
       .whenMatchedUpdate(set={
           "status": "s.status",
           "aggregate_version": "s.aggregate_version",
           "ingested_at_ts": "s.ingested_at_ts",
           "content_hash": "s.content_hash"})
       .whenNotMatchedInsertAll()
       .execute())
else:
    (df_dedup.write
       .partitionBy("tenant_id")
       .format("delta")
       .mode("overwrite")
       .save(silver_path))

# Fix 3: stronger idempotency check (content checksum, not row count)
sorted_sig = spark.read.format("delta").load(silver_path) \
    .select("dedup_key","content_hash") \
    .orderBy("dedup_key").toPandas()
checksum = hashlib.sha256(
    sorted_sig.to_csv(index=False).encode()).hexdigest()
# Run pipeline twice, compare checksums — true idempotency
```

### What changes in production

The demo's row-count check is the single weakest invariant. Row count is monotonically correlated with idempotency only because the demo has no late-arriving or out-of-order events. In production, the invariant you actually need is: **the silver table is a function of the input stream up to a watermark**. The content-hash check captures that — re-running with the same input produces the same hash, regardless of which rows are present.

Three other shifts happen the moment you cross from `local[2]` to a 30k-tenant cluster:

1. **Partition pruning becomes a cost lever, not a nicety.** Without `partitionBy("tenant_id", "dt")`, every silver read scans the entire table. With 30k tenants × 730 days, that's millions of partitions and a multi-TB scan per query. The audit's `partitionBy("tenant_id")` fix is the minimum; production needs `dt` as a coarser partition and ZORDER on `(execution_id, test_case_id)` inside each tenant/day partition.
2. **The merge becomes the bottleneck, not the dedup.** At 30k tenants, MERGE-on-business-key with 20M daily rows triggers shuffle-heavy file rewrites. Pre-aggregate by date, use Delta's `optimizedWrite` + `autoCompact`, and consider bucketing by `tenant_id` to keep hot-key partitions manageable.
3. **Schema evolution becomes a deployment.** The demo never adds a column. Production does, on a quarterly cadence. Without `delta.columnMapping.mode = 'name'` and a contract-tested producer CI, adding a column silently breaks consumers. This is a *catalog* problem, not a *code* problem — the fix is governance, not Spark config.

---

## Prototype B — Flakiness SQL Runner

**What it proves:** Per-test-case stability metrics over ≥5 runs.

### PASS
- Window partition keys correct.
- `LAG(status)` over `ORDER BY completed_at, execution_id` is right for transition detection.
- `WHERE run_count >= 5` is a sensible statistical minimum.
- `NULLIF(r.failed_first_attempts, 0)` correctly avoids divide-by-zero.

### BUG
1. **`IFF()` is Databricks-specific.** Fails on vanilla Spark, Presto, Trino. Replace with `CASE WHEN ... THEN ... ELSE ... END`. (Same issue applies to Prototype C.)
2. **`transition_rate` denominator is wrong / misleading.** The first execution of every test has `previous_status = NULL` → contributes NULL. Average treats NULL as missing. That's defensible, but the name is misleading — it's "rate of executions where status differs from previous execution, excluding first." Document it.
3. **`completed_at` is a string.** Same as Prototype A: lexicographic sort works for ISO 8601 but breaks for sloppy formats.
4. **`status IN ('PASSED','FAILED')` excludes 'SKIPPED','ERROR','TIMEOUT'.** Real Katalon statuses likely include these. Silently treated as missing data → `transition_rate` denominator drops → masks flakiness. Make it config-driven.
5. **`recovered_on_retry` uses `reverse_attempt_rank = 1 AND status = 'PASSED'`** — counts any final-passed test as recovered. A test that ran 5 attempts and ended PASSED is counted as recovered even if it failed 4 times. Probably what you want, but document it.
6. **No assertion that test data has multiple environments for the same test.** Schema sound; test data too narrow.

### RISK
- **`ORDER BY ... NULLS LAST`** is ANSI; safe on DBR ≥9.0, but Hive 2.x silently ignores it.
- **`AVG(IFF(...))` returns DOUBLE** — overflow risk on `BIGINT` columns over billions of rows. Use `try_divide` and explicit cast.
- **No `tenant_id` predicate.** Full scan over 30k tenants × all-time data is expensive.
- **`transition_rate` biased by execution cadence.** Bucket by day/week.
- **Window over `attempt_rank = 1` then LAG over the SAME partition** — but LAG operates on the smaller filtered set. Fine, but ties in `completed_at` get arbitrary `execution_id` tiebreaking.

### FIX

```sql
-- Replace IFF with portable CASE WHEN
WITH base AS (
  SELECT
    CAST(tenant_id AS STRING) AS tenant_id,
    CAST(project_id AS STRING) AS project_id,
    test_case_id, environment_hash,
    execution_id, attempt_id, status,
    TO_TIMESTAMP(completed_at) AS completed_at,
    ROW_NUMBER() OVER (
      PARTITION BY tenant_id, project_id, test_case_id,
                   environment_hash, execution_id
      ORDER BY attempt_id) AS attempt_rank,
    ROW_NUMBER() OVER (
      PARTITION BY tenant_id, project_id, test_case_id,
                   environment_hash, execution_id
      ORDER BY attempt_id DESC) AS reverse_attempt_rank
  FROM test_results
  WHERE status IN ('PASSED','FAILED','SKIPPED','ERROR')  -- explicit allow-list
),
first_attempts AS (
  SELECT *,
    LAG(status) OVER (
      PARTITION BY tenant_id, project_id, test_case_id, environment_hash
      ORDER BY completed_at, execution_id) AS previous_status
  FROM base WHERE attempt_rank = 1
),
execution_outcomes AS (
  SELECT tenant_id, project_id, test_case_id, environment_hash,
         execution_id,
         MAX(CASE WHEN attempt_rank=1 AND status='FAILED' THEN 1 ELSE 0 END)
           AS first_failed,
         MAX(CASE WHEN reverse_attempt_rank=1 AND status='PASSED'
                  THEN 1 ELSE 0 END) AS final_passed,
         COUNT(*) AS attempt_count
  FROM base
  GROUP BY 1,2,3,4,5
),
stability AS (
  SELECT tenant_id, project_id, test_case_id, environment_hash,
         COUNT(*) AS run_count,
         AVG(CASE WHEN status='FAILED' THEN 1.0 ELSE 0.0 END)
           AS first_attempt_failure_rate,
         AVG(CASE
               WHEN previous_status IS NULL THEN NULL
               WHEN status <> previous_status THEN 1.0
               ELSE 0.0
             END) AS transition_rate
  FROM first_attempts
  GROUP BY 1,2,3,4
),
recovery AS (
  SELECT tenant_id, project_id, test_case_id, environment_hash,
         SUM(first_failed) AS failed_first_attempts,
         SUM(CASE
               WHEN first_failed=1 AND attempt_count>1 AND final_passed=1
               THEN 1 ELSE 0 END) AS recovered_on_retry
  FROM execution_outcomes
  GROUP BY 1,2,3,4
)
SELECT s.tenant_id, s.project_id, s.test_case_id, s.environment_hash,
       s.run_count,
       ROUND(s.first_attempt_failure_rate, 4) AS first_attempt_failure_rate,
       ROUND(s.transition_rate, 4) AS transition_rate,
       COALESCE(r.recovered_on_retry, 0) AS recovered_on_retry,
       ROUND(
         CAST(COALESCE(r.recovered_on_retry, 0) AS DOUBLE)
         / NULLIF(r.failed_first_attempts, 0), 4
       ) AS retry_recovery_rate
FROM stability s
LEFT JOIN recovery r
  USING (tenant_id, project_id, test_case_id, environment_hash)
WHERE s.run_count >= 5
ORDER BY s.transition_rate DESC NULLS LAST, s.run_count DESC
```

### What changes in production

This prototype is the one the panel will scrutinize hardest, because flakiness is a metric a smart lazy engineer can game. Three production realities change the picture:

1. **The `run_count >= 5` floor is too low for flakiness decisions.** Five executions is noise. The production floor is closer to 30, and even then a Bayesian shrinkage prior toward 0.5 is required for tests that haven't yet accumulated evidence — otherwise a test that's run twice (P, F) shows `transition_rate = 1.0` and triggers an alert. That's the kind of false positive that erodes trust in the metric and gets the whole feature turned off.
2. **Window functions over `attempt_rank = 1` only work if `attempt_id` is the source of truth, not the platform's rendering.** A test framework that retries internally and emits one event with the final status hides flakiness upstream. The metric sees a stable test; the customer sees flakes. The fix is at the source: require producers to emit a stream of attempt events, not a single rolled-up status. That's a contract, not a query.
3. **`environment_hash` is both the right call and the wrong default.** It correctly buckets across environments, but at 30k tenants × 5 environments × 1000s of tests, the GROUP BY cardinality explodes. Production keeps `environment_hash` as the key but pre-aggregates to `(tenant_id, project_id, test_case_id, environment_hash, dt)` and computes flakiness metrics off the pre-aggregate. The query becomes cheap enough to run hourly; the metric becomes visible to product managers without an analytics request.

## Prototype C — Reconciliation (Producer vs Accepted vs Silver vs Served)

**What it proves:** Four-layer count reconciliation surfaces drift between producer, ingestion, silver, and served.

### PASS
- Four-layer reconciliation is the right surface area for a "data never gets lost" guarantee.
- `LEFT JOIN` from manifest ensures tenants with no producer events are still surfaced.
- `CASE WHEN` portable (vs `IFF`).

### BUG
1. **Inconsistent style — `IFF()` and `CASE WHEN` mixed.** Pick one. Any `IFF()` will fail on non-Databricks compute.
2. **No partition pruning predicate.** Without `WHERE dt BETWEEN ...` the recon runs over all-time data every run. Add a mandatory `dt` filter or break by date.
3. **Empty-case collapse.** A tenant with all four layers at zero is a true empty state; one with `producer > 0` but `silver = 0` is a leak risk. Recon must distinguish these. Use `COUNT_IF(layer='producer')` per layer so you can report `producer - silver != 0`.
4. **Float comparison on counts.** If any layer uses an estimated count (`ANALYZE TABLE` not fresh), you'll get drift. Always use exact counts: `SELECT COUNT(*) FROM table WHERE tenant_id = ...`.
5. **`NULL` row in `manifest`.** A tenant with NULL `tenant_id` aggregates into a "ghost tenant" row, masking real leaks. Filter `WHERE tenant_id IS NOT NULL` or surface explicitly.
6. **`tenant_id` as STRING but downstream JOIN keys may be LONG.** Implicit cast succeeds with ANSI mode off, fails with `ANSI_NUMERIC_ARITHMETIC` or coerces wrong. Enforce explicit types.

### RISK
- **No SLO on the recon job itself.** A reconciliation that takes 6 hours is useless daily. Add `runtime_minutes` SLO + alert.
- **No alert thresholds defined.** "They should match" is not an alert. Define: `abs(producer_count - silver_count) > 100 OR pct_delta > 0.1%` → page.
- **No late-arriving window.** A producer event ingested today might not be in silver for 2 hours. Recon should use an "as-of" timestamp + grace window.
- **No dedup of recon rows.** If a tenant gets reprocessed, recon may double-count. Use `MERGE` into a `recon_status` Delta table keyed on `(tenant_id, dt)`.
- **Recon only catches counts, not content.** A row in silver with wrong values still reconciles green. Add content hash check on a sample.
- **Cross-tenant leak detection missing.** A row with `tenant_id='t_001'` in producer ending up with `tenant_id='t_002'` in silver — counts balance, privacy violated. Add a sample check.

### FIX

```sql
WITH producer AS (
  SELECT tenant_id,
         CAST(COUNT(*) AS BIGINT) AS row_count
  FROM test_events_producer
  WHERE dt BETWEEN :start_dt AND :end_dt
    AND tenant_id IS NOT NULL
  GROUP BY tenant_id
),
accepted AS (
  SELECT tenant_id, CAST(COUNT(*) AS BIGINT) AS row_count
  FROM test_events_accepted
  WHERE dt BETWEEN :start_dt AND :end_dt AND tenant_id IS NOT NULL
  GROUP BY tenant_id
),
silver AS (
  SELECT tenant_id, CAST(COUNT(*) AS BIGINT) AS row_count
  FROM delta.`s3://katalon-silver/test_results`
  WHERE dt BETWEEN :start_dt AND :end_dt AND tenant_id IS NOT NULL
  GROUP BY tenant_id
),
served AS (
  SELECT tenant_id, CAST(COUNT(*) AS BIGINT) AS row_count
  FROM served_test_results
  WHERE dt BETWEEN :start_dt AND :end_dt AND tenant_id IS NOT NULL
  GROUP BY tenant_id
),
manifest AS (
  SELECT tenant_id FROM producer
  UNION SELECT tenant_id FROM accepted
  UNION SELECT tenant_id FROM silver
  UNION SELECT tenant_id FROM served
)
SELECT m.tenant_id,
       COALESCE(p.row_count,0) AS producer_n,
       COALESCE(a.row_count,0) AS accepted_n,
       COALESCE(s.row_count,0) AS silver_n,
       COALESCE(v.row_count,0) AS served_n,
       (COALESCE(p.row_count,0) - COALESCE(s.row_count,0)) AS producer_minus_silver,
       CASE
         WHEN COALESCE(p.row_count,0) = 0 THEN NULL
         ELSE ROUND(ABS(COALESCE(p.row_count,0) - COALESCE(s.row_count,0))
                    / COALESCE(p.row_count,0), 6)
       END AS pct_delta_producer_silver
FROM manifest m
LEFT JOIN producer p USING (tenant_id)
LEFT JOIN accepted a USING (tenant_id)
LEFT JOIN silver  s USING (tenant_id)
LEFT JOIN served  v USING (tenant_id)
```

```sql
-- Cross-tenant leak spot-check (separate job, sampled)
SELECT producer.tenant_id AS producer_tenant,
       silver.tenant_id  AS silver_tenant,
       COUNT(*) AS leaked_rows
FROM delta.`s3://katalon-silver/test_results` silver
JOIN test_events_producer producer
  ON producer.event_id = silver.event_id
WHERE producer.tenant_id <> silver.tenant_id
  AND producer.dt BETWEEN :start_dt AND :end_dt
GROUP BY 1,2
HAVING COUNT(*) > 0
```

### What changes in production

Recon is the prototype most likely to **silently fail open** — produce a green result while a real leak is happening. Three production realities change this:

1. **Recon must run per tenant tier, not globally.** A 30k-tenant recon over all-time data exceeds daily SLO within the first quarter. Split: tier-1 enterprises get hourly recon against a 24h window; tier-2 gets daily against a 7d window; tier-3 gets weekly. Each tier has its own alert threshold calibrated to its volume.
2. **Recon catches drift but not intent.** A row in `silver` with `tenant_id='t_001'` that came from a producer event with `tenant_id='t_002'` reconciles green because the row count is identical at the tenant level. The cross-tenant leak query is the only place intent is checked, and it must run on every commit, not as a sample. Otherwise the next leak looks like a clean recon.
3. **Recon status must surface in the product, not just the data team's dashboard.** A recon job that fires an alert to the data team but shows green in the customer-facing dashboard is a worse failure than no recon at all — it gives the customer false confidence. The recon status is itself a data product with its own SLO and owner.

## Prototype D — Retrieval Eval Harness

**What it proves:** Compares lexical, hybrid, and a deliberately leaky retriever on `recall@k`, MRR, and cross-tenant leakage.

### PASS
- Three retriever design (lexical, hybrid, leaky) is a smart way to validate the eval harness itself — if the leaky retriever doesn't show high leakage, the harness is broken.
- MRR + recall@k are the right pair.
- Cross-tenant leakage as a first-class metric shows security awareness.

### BUG
1. **`recall@k` with empty relevant list returns 0.0** — the well-known evaluation pitfall. If a query has no relevant docs in your ground truth (corpus incomplete), `recall@k = 0` makes the retriever look bad when ground truth is incomplete. Fix: skip and report `coverage` separately.
2. **Hash collision risk in `v2_hybrid`** if `doc_env_42` appears in multiple tenants. Hash function must include `tenant_id` in the input.
3. **`recall@k` typically uses `set(top_k_results) ∩ set(relevant_docs)`** — but if the retriever returns a doc twice (deduped by ID but not by content), `len(intersection)` double-counts. Dedupe by `doc_id` BEFORE computing recall.
4. **MRR uses reciprocal rank of FIRST relevant doc.** If two relevant docs tie at rank 1, count once. Make sure ground truth is a SET, not a ranked list.
5. **No seed for `random` in retriever ranking tiebreaking.** Lexical and hybrid tie on score → random tiebreaking → eval non-deterministic.
6. **Empty queries.** What if `query_text=""`? Lexical returns empty; hybrid returns something; eval records `recall@10 = 0`. Add `if not query_text: skip`.
7. **Tenant isolation assumption.** If the index is global and you filter post-hoc, a malicious tenant can probe by injecting many queries. Consider per-tenant indexes; **and** assert both at index-time and eval-time.

### RISK
- **Ground truth construction is the silent killer.** If `relevant_docs` was built by the same lexical retriever, you have circular evaluation. Document source.
- **Sample size.** 50 queries fine for demo, useless for 30k-tenant product. Stratified sampling.
- **Offline metrics vs online behavior.** High recall@k on 50 queries may have terrible latency on full corpus. Add `latency_p95_ms`.
- **Hash collisions are tenant-boundary disasters.** Use `hashlib.sha256` or `xxhash`, not Python `hash()` (randomized per process).
- **No corpus versioning.** If the index changes between runs, metrics aren't comparable. Hash the corpus and pin it.
- **`recall@k` denominator varies per query.** Macro-average vs micro-average matters. Report both.

### FIX

```python
import hashlib, random
from collections import defaultdict

random.seed(42)

def hash_doc(tenant_id: str, doc_id: str) -> str:
    # NEVER hash doc_id alone — must include tenant for cross-tenant safety
    return hashlib.sha256(f"{tenant_id}::{doc_id}".encode()).hexdigest()

def recall_at_k(retrieved_ids, relevant_ids, k):
    if not relevant_ids:
        return None  # signal: skip this query
    return len(set(retrieved_ids[:k]) & set(relevant_ids)) / len(relevant_ids)

def mrr(retrieved_ids, relevant_ids):
    if not relevant_ids:
        return None
    for rank, doc_id in enumerate(retrieved_ids, start=1):
        if doc_id in relevant_ids:
            return 1.0 / rank
    return 0.0

def evaluate(retriever, eval_set, k=10):
    per_query_recall, per_query_mrr = [], []
    skipped_empty_gt = 0
    leakage_count = 0
    for q in eval_set:
        if not q["query_text"].strip():
            continue
        retrieved = retriever(q["query_text"], tenant_id=q["tenant_id"], k=k)
        cross_tenant = [d for d in retrieved if d["tenant_id"] != q["tenant_id"]]
        if cross_tenant:
            leakage_count += 1
        same_tenant = [d for d in retrieved if d["tenant_id"] == q["tenant_id"]]
        r = recall_at_k([d["doc_id"] for d in same_tenant],
                        set(q["relevant_doc_ids"]), k)
        m = mrr([d["doc_id"] for d in same_tenant],
                set(q["relevant_doc_ids"]))
        if r is not None:
            per_query_recall.append(r)
        else:
            skipped_empty_gt += 1
        if m is not None:
            per_query_mrr.append(m)
    n_eff = len(per_query_recall)
    return {
        "recall_at_k_mean": (sum(per_query_recall) / n_eff) if n_eff else None,
        "mrr_mean": (sum(per_query_mrr) / len(per_query_mrr)) if per_query_mrr else None,
        "effective_query_count": n_eff,
        "skipped_empty_ground_truth": skipped_empty_gt,
        "ground_truth_coverage": n_eff / (n_eff + skipped_empty_gt)
            if (n_eff + skipped_empty_gt) else None,
        "cross_tenant_leakage_queries": leakage_count,
        "leakage_rate": leakage_count / len(eval_set) if eval_set else 0,
    }
```

### What changes in production

The eval harness is the prototype most likely to be **adopted uncritically**. Three production realities change this:

1. **Offline recall@k tells you nothing about answer quality.** A retriever with `recall@10 = 0.9` can still surface irrelevant docs in the top-3, and the LLM uses them. The harness needs end-task metrics: was the answer grounded in retrieved evidence? Did the citation resolve to a real artifact? Was the action the agent took reversible? These metrics come from a separate eval set, ideally human-labeled, and the offline recall is a *necessary but not sufficient* filter.
2. **Ground truth constructed from the same index is circular.** If your `relevant_doc_ids` were sourced by running lexical retrieval and annotating the top hits, you have a retriever that scores perfectly against itself. The fix is to source ground truth from a different signal — customer support tickets linking to the right artifact, or expert adjudication. Otherwise the eval numbers are meaningless and you ship a regression.
3. **Cross-tenant leakage in eval must hit zero, but a non-zero hit rate in staging is a launch blocker, not a warning.** The audit's leakage detector is correct in spirit but undersized for production — it checks `result.tenant_id != query.tenant_id`, which catches direct leaks but misses gradient leakage (an embedding that *resembles* another tenant's content) and indirect leakage (a doc authored in one tenant's workspace that references another tenant's identifier). Both require additional checks: embedding-space similarity audits, and post-retrieval policy filters that re-check the doc's tenant against the query's tenant at the storage layer, not the index layer.

## Prototype E — Idempotent Outbox for Agent Tool Calls

**What it proves:** Agent tool calls are deduped by content hash, restricted to an ALLOWED set, gated by a per-tenant allow-list, persisted atomically.

### PASS
- ALLOWED set is the right control plane.
- Tenant allow-list prevents cross-tenant tool access.
- Idempotency key from call contents is the canonical pattern.
- `sqlite3` schema translates cleanly to Postgres/DynamoDB.

### BUG
1. **SQLite write race condition.** Two concurrent submits with the same key both read "no row," both insert, both commit. The `UNIQUE` constraint catches at COMMIT time — one fails with `IntegrityError` — but failure handling is missing. Use `INSERT ... ON CONFLICT DO NOTHING` + check `rowcount`.
2. **Hash collisions on idempotency key.** If you use SHA-256 of `(tool_name, tenant_id, payload_json)`, collisions are practically impossible — but if you use MD5 or Python `hash()`, two distinct payloads could share a key and the second call would be silently deduplicated. Use SHA-256; always include `tenant_id`.
3. **`payload_json` normalization.** `{"x":1,"y":2}` vs `{"y":2,"x":1}` → different strings → different hashes → no dedup. Normalize with `json.dumps(payload, sort_keys=True, separators=(',', ':'))`.
4. **`tool_name` not in the idempotency key.** If two tools accept the same payload shape and you forget `tool_name`, they collide. Always include it.
5. **Tenant allow-list check ordering matters.** If you check idempotency first, a denied call still creates a row in the outbox (just doesn't execute). Decide if that's desired.
6. **No TTL on idempotency keys.** A 90-day-old call could be replayed. Add `created_at` and purge N days.
7. **`sqlite3` default isolation is `deferred`.** Two concurrent transactions on the same key serialize. Use WAL mode.
8. **Side effect outside transaction.** The whole point of the outbox pattern is: record intent in transaction, execute side effect OUTSIDE, then mark completed in a second transaction. The demo writes once and considers it done.
9. **No atomic `pending` → `completed` transition.** Classic outbox requires a state column. If tool fails after row is committed, outbox shows "succeeded" but reality is "failed."

### RISK
- **SQLite single-writer** at agent scale becomes a bottleneck. Migrate to Postgres/DynamoDB.
- **No retries / no dead-letter.** Failed calls have no retry policy. Add max retry count and dead-letter table.
- **Tenant allow-list is a static set.** In prod it's per-tenant config with `effective_at` / `expires_at`.
- **Tool name in ALLOWED but payload doesn't match allowed schema.** Schema validation is the missing layer.
- **PII in tool calls** stored unencrypted in the outbox.
- **No rate limiting per tenant.**
- **Audit log missing.** SOC 2 / GDPR require immutable audit, not just a mutable SQLite row.
- **`tenant_id` not bound to the API caller.** A bug or attack can pass any `tenant_id`. Bind to authenticated principal, never to a request parameter.

### FIX

```python
import sqlite3, json, hashlib, time
from contextlib import contextmanager

ALLOWED_TOOLS = {"search_kb", "create_ticket", "lookup_user"}
TENANT_ALLOWLIST = {"t_001", "t_002"}

@contextmanager
def get_conn(db_path):
    conn = sqlite3.connect(db_path, isolation_level=None)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
    finally:
        conn.close()

def make_idempotency_key(tool_name, tenant_id, payload):
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"),
                           ensure_ascii=False)
    h = hashlib.sha256()
    h.update(f"{tool_name}|{tenant_id}|{canonical}".encode())
    return h.hexdigest()

def submit_tool_call(conn, *, tool_name, tenant_id, payload, principal_id):
    assert tenant_id in TENANT_ALLOWLIST, f"tenant {tenant_id} not allowed"
    assert tool_name in ALLOWED_TOOLS, f"tool {tool_name} not in allowlist"
    # In prod: derive tenant_id from authenticated session, not the arg
    idem_key = make_idempotency_key(tool_name, tenant_id, payload)
    cur = conn.execute("""
        INSERT INTO outbox
          (idem_key, tool_name, tenant_id, principal_id, payload_json,
           state, created_at, expires_at)
        VALUES (?, ?, ?, ?, ?, 'pending', ?, ?)
        ON CONFLICT(idem_key) DO NOTHING
    """, (idem_key, tool_name, tenant_id, principal_id,
          json.dumps(payload), int(time.time()),
          int(time.time()) + 7*24*3600))
    if cur.rowcount == 0:
        row = conn.execute(
            "SELECT id, state, result_json FROM outbox WHERE idem_key=?",
            (idem_key,)).fetchone()
        return {"outbox_id": row[0], "state": row[1], "deduplicated": True}
    return {"outbox_id": cur.lastrowid, "state": "pending", "deduplicated": False}

def mark_completed(conn, outbox_id, result):
    conn.execute("""
        UPDATE outbox
        SET state='completed', result_json=?, completed_at=?
        WHERE id=? AND state='pending'
    """, (json.dumps(result), int(time.time()), outbox_id))

def mark_failed(conn, outbox_id, error, retry_count):
    new_state = 'dead_letter' if retry_count >= 3 else 'failed'
    conn.execute("""
        UPDATE outbox
        SET state=?, error=?, retry_count=?, last_retry_at=?
        WHERE id=?
    """, (new_state, error, retry_count, int(time.time()), outbox_id))
```

### What changes in production

The outbox is the prototype the panel will push hardest on, because **the bug it produces is the most damaging** — a side effect that fires twice because two retries collided on the same idempotency key. Three production realities change this:

1. **The outbox is a state machine, not a row.** Production needs `pending → applied → completed` with explicit transitions, timeouts on each state, and a drainer process that picks up rows stuck in `pending` past the SLA. The demo collapses the state to "row exists" which works at one agent's pace but fails at 10k agents per minute because there's no recovery for in-flight rows that crash mid-tool-execution.
2. **The audit log is a regulatory artifact, not a debugging convenience.** The demo's audit table is a SQLite row, which the panel will accept for the demo but not for production. SOC 2 / GDPR require the audit log to be append-only, signed (HMAC or signed event), and replicated to a separate storage tier with retention tied to legal hold. The same content; a different trust model.
3. **`tenant_id` from the request is a privilege escalation waiting to happen.** The demo accepts `tenant_id` as a parameter. Production binds `tenant_id` to the authenticated principal — the OAuth token, the mTLS identity, the workload identity — and refuses any tool call whose declared `tenant_id` doesn't match. This is the single change that turns the outbox from "demo" to "production-safe," and it's the one most likely to be skipped by someone reading the demo quickly.

## Cross-Cutting Findings

| Concern | Severity | Notes |
|---|---|---|
| **`tenant_id` as `STRING` everywhere** | High | 30k tenants × string keys bloats shuffle. Consider `BIGINT` with a tenant dimension table. JOINs also break on case (`T_001` vs `t_001`). |
| **No `dt` / `event_date` partition** | High | All five prototypes scan all-time data. Production needs daily partitioning + ZORDER on `tenant_id, execution_id`. |
| **No observability / SLO** | High | None emit metrics. A pipeline that ships without `latency_p95`, `freshness_lag`, `error_rate` gets deleted in 6 months. |
| **Demo fixtures don't reflect prod cardinality** | High | 12 rows, 1 tenant, 1 environment. Synthetic data should match tenant size distribution (power-law: few mega, many tiny). |
| **No schema contract / Delta schema enforcement** | Medium | Use `delta.columnMapping.mode = 'name'` and `delta.enableChangeDataFeed`. |
| **No unit tests for edge cases** | Medium | Single-row tables, NULL tenant_id, empty partitions, all-FAILED tests, retries with same attempt_id. |
| **`random.seed` set but not all RNG sources seeded** | Medium | Python `random`, `numpy`, `torch`, `hash` — each needs seeding for reproducibility. |
| **No row-level filters in asserts** | Medium | Count checks should also validate `WHERE tenant_id = :tenant` row counts, not just totals. |
| **Security: `tenant_id` from request, not from session** | Critical (D) | Any path where `tenant_id` is a function arg rather than derived from authenticated session is a privilege escalation vector. |

---

## Top 5 Issues, Ranked by Production Severity

1. **Prototype E outbox race condition** (concurrent submits with same key → double side effect).
2. **Prototype B `IFF()` portability** (will break on any non-DBR compute).
3. **Prototype A `monotonically_increasing_id()` as tiebreaker** (silent ordering corruption).
4. **Prototype D empty ground-truth + hash collision** (eval harness lies to you).
5. **Prototype C no partition pruning** (reconciliation job times out on month 1).