# 10.1 — Pricing Models

> **Section 10 · Pricing & Cost Optimization · Lecture 10.1 · 5:55**

## 🎯 What you will learn

- Every BigQuery pricing dimension: storage, queries, DML, DDL, and APIs
- On-demand vs capacity (slot) vs enterprise editions
- Free tiers and the pricing quotas you should know
- How the bill is actually calculated
- Building a cost model for a real workload

---

## 🧠 Concept

BigQuery has **four** billable dimensions. Understanding all four is the difference between
predictable and surprising bills.

| Dimension | Charged for | Typical rate |
|-----------|-------------|--------------|
| **Storage** | Logical bytes (and physical for capacity-optimized) | $0.02 / GiB / month (active) |
| **Query processing** | Bytes scanned by on-demand queries | $6.25 / TiB |
| **DML** | Bytes modified + bytes scanned | $6.25 / TiB (scanned) + $0.01/GiB (modified) |
| **DDL / APIs** | Schema updates, table ops, BigQuery API calls | $0.01 / GiB modified |

---

## 🧠 Storage pricing

| Storage class | Rate | Applies to |
|---------------|------|-----------|
| Active logical | $0.02 / GiB / month | Standard tables, streaming buffer |
| Long-term logical | $0.01 / GiB / month | Tables in long-term storage (after 30 days) |
| Active physical | $0.04 / GiB / month | Capacity-optimized tables |
| Long-term physical | $0.02 / GiB / month | Capacity-optimized in long-term |
| Snapshot storage | $0.026 / GiB / month | Table snapshots |
| Materialized view storage | Same as the underlying table | |

```bash
# Move a table to long-term storage
bq update --dml_allow_policies \
  --set_partition_expiration_days=0 \
  YOUR_PROJECT_ID:curated.old_orders
```

```python
table = client.get_table("YOUR_PROJECT_ID.curated.old_orders")
table.expires = None
table.labels = {**table.labels, "storage": "long-term"}
client.update_table(table, update_mode="update_fields")
```

💡 **Long-term storage is half the price but you lose the fast first byte.** Moving a table is
free but takes up to a few hours to complete.

---

## 🧠 Query pricing

### On-demand

```
Cost = (bytes_scanned / 1 TiB) × $6.25
```

- $6.25 per TiB of data **scanned**
- The first 1 TiB of data processed per month is **free** (on-demand)
- **No cost for bytes returned** — only bytes scanned
- Results cached for 24 hours are free

💡 **The free 1 TiB is per month, per billing account.** It resets on the 1st.

### Capacity (slot commitments)

```
Cost = (slots × hours × rate) + (bytes_scanned × on-demand rate)
```

| Edition | Slot-hour rate | Best for |
|---------|----------------|----------|
| Standard | $0.04 / slot-hour | Steady, predictable workloads |
| Enterprise | $0.06 / slot-hour | Lower latency, better isolation |
| Enterprise Plus | $0.10 / slot-hour | Very low latency, highest isolation |

- A **slot** = 1 vCPU + 4 GB RAM
- 1 slot-hour = 1 slot for 1 hour
- Baseline: 100 slots = 100 slot-hours/hour
- You pay for **reserved** capacity even if idle; excess usage is billed on-demand

```bash
# Reserve capacity
gcloud bigquery reservations create \
  --project=YOUR_PROJECT_ID \
  --location=US \
  --reservation=my-reservation \
  --capacity-type=hedge \
  --slots=500 \
  --edition=standard

# Assign projects to the reservation
gcloud bigquery reservations assignments create \
  --project=YOUR_PROJECT_ID \
  --location=US \
  --reservation=my-reservation \
  --assignment=project-YOUR_PROJECT_ID \
  --job-type=QUERY
```

```python
# Use the reservation
job_config = bigquery.QueryJobConfig(
    reservation="projects/YOUR_PROJECT_ID/locations/US/reservations/my-reservation"
)
```

💡 **Capacity pricing is a commitment.** Only move to it when your on-demand bill is stable
above roughly 500–1,000 slot-hours/month. Below that, on-demand is almost always cheaper.

### Choosing a model

| Workload | Model | Why |
|----------|-------|-----|
| Sporadic, low volume | On-demand | No idle cost |
| Steady batch pipelines | Capacity | Predictable, cheaper at volume |
| Latency-sensitive BI | Enterprise / Enterprise Plus | Lower queueing |
| Unpredictable spikes | On-demand + a small reservation | Hedge |

---

## 🧠 DML and DDL pricing

| Operation | Cost |
|-----------|------|
| `INSERT` / `UPDATE` / `DELETE` | $6.25 / TiB **scanned** + $0.01 / GiB **modified** |
| `MERGE` | Same as DML |
| `TRUNCATE` | No charge |
| `CREATE TABLE` / `DROP TABLE` | Free (DDL), but **storage** counts |
| `ALTER TABLE ADD COLUMN` | $0.01 / GiB of data modified |
| `UPDATE` on a non-partitioned table | Rewrites the whole table — expensive |
| `CREATE MATERIALIZED VIEW` | Storage + a full refresh of the base data |
| Table snapshot | Snapshot storage rate |
| `EXPORT DATA` | Query bytes + storage in GCS |
| BigQuery Storage Write API | $0.01 / GiB written + query costs |

💡 **`ALTER TABLE ADD COLUMN` is not free on a large table.** It rewrites the schema metadata
and can be slow on multi-terabyte tables. Prefer creating a new table when the change is large.

### Streaming insert pricing

| Item | Cost |
|------|------|
| First 1 GB per table per day | **Free** |
| After that | $0.01 per 200 MB |
| Streaming buffer storage | Active storage rate ($0.02 / GiB / month) |
| Storage Write API (first 2 GB/day/table) | Free, then $0.01 / GiB |

---

## 🧠 API pricing

| API | Rate |
|-----|------|
| BigQuery API (job queries) | $0.01 / 1000 requests per table scanned, + query bytes |
| BigQuery Storage API reads | $0.01 / TiB (minimum 10 MB per request) |
| BigQuery Storage Write API | $0.01 / GiB |
| Bigtable API | Separate pricing |
| `insertAll` / `insertRows` | $0.01 per 1000 rows per table |

---

## 🧠 Free tier and quotas

| Item | Free allowance |
|------|----------------|
| Storage | 10 GB / month |
| Query bytes (on-demand) | 1 TiB / month |
| Streaming inserts | 1 GB / day / table |
| Storage Write API | 2 GB / day / table |
| Continuous queries | 1 TiB / month scanned |

**Free tier is per billing account**, not per project, and it applies across all projects in
the account.

### Quotas worth knowing

| Quota | Typical value |
|-------|---------------|
| On-demand bytes processed per table per day | 10 TiB (raiseable) |
| Maximum bytes billed per table per day | 50 TiB (raiseable) |
| Interactive query timeout | 6 hours |
| Maximum bytes per query | 5 TiB (raiseable) |
| Rows per streaming insert | 1,000 |
| Streaming insert size | 10 MB |
| Tables per project | 20,000 (raiseable) |
| Queries per second | Project-dependent |
| Concurrent queries | 1,000 |

---

## 🛠️ Hands-On

### 1. Estimate a query's cost before running it

```python
def estimate_cost(sql: str, project: str = "YOUR_PROJECT_ID") -> dict:
    client = bigquery.Client(project=project)
    job_config = bigquery.QueryJobConfig(dry_run=True, use_query_cache=False)
    job = client.query(sql, job_config=job_config)

    total_bytes = job.total_bytes_processed or 0
    tib = total_bytes / (1024**4)
    free_remaining = max(0, 1 - (get_monthly_used_tib()))
    billable_tib = max(0, tib - free_remaining)

    return {
        "bytes": total_bytes,
        "tib": round(tib, 4),
        "est_cost_usd": round(billable_tib * 6.25, 4),
        "note": "first 1 TiB/month is free",
    }
```

### 2. Read the current month's cost from the billing export

```bash
bq query --use_legacy_sql=false --format=pretty '
SELECT
  service.description AS service,
  SUM(cost) AS total_cost,
  SUM(credits) AS total_credits,
  SUM(cost + credits) AS net_cost
FROM `YOUR_PROJECT_ID.billing.gcp_billing_export_v1_0_6A5C4B7E_9F2D_1C3A_8E5B_2D7F_6A9C4B7E9F2D1C3A8E5B2D7F6A9C4B7E`
WHERE usage_start_time >= TIMESTAMP("2026-10-01")
GROUP BY service
ORDER BY net_cost DESC'
```

```python
# A simpler, self-contained cost tracker in BigQuery
client.query(
    """
    CREATE TABLE IF NOT EXISTS `YOUR_PROJECT_ID.monitoring.query_costs` (
      query_id STRING,
      run_at TIMESTAMP,
      bytes_billed INT64,
      est_cost_usd FLOAT64,
      job_config STRING
    )
    """
)
```

### 3. A cost-tracking wrapper

```python
def run_tracked(sql: str, label: str = "") -> list[bigquery.Row]:
    """Run a query and record its cost into a BigQuery audit table."""
    client = get_client()

    # 1. Dry run
    dry = client.query(
        sql, job_config=bigquery.QueryJobConfig(dry_run=True, use_query_cache=False)
    )
    est_bytes = dry.total_bytes_processed or 0

    # 2. Execute
    job = client.query(sql)
    rows = list(job.result())

    # 3. Record
    client.insert_rows_json(
        client.dataset("monitoring").table("query_costs"),
        [
            {
                "query_id": job.query_id,
                "run_at": datetime.now(timezone.utc).isoformat(),
                "bytes_billed": job.total_bytes_billed or 0,
                "est_cost_usd": (est_bytes / 1024**4) * 6.25,
                "job_config": label,
            }
        ],
    )
    return rows
```

### 4. Model a workload's monthly cost

```python
"""
Cost model for the RetailMart pipeline.
"""

# --- Storage ---
raw_gb = 800          # growing 1 GB/day
staging_gb = 50
curated_gb = 900
mart_gb = 120

storage_cost = (raw_gb * 0.02 + staging_gb * 0.02 + curated_gb * 0.01 + mart_gb * 0.02)

# --- Batch queries (daily) ---
daily_scan_gb = 120
dml_modified_gb = 60

daily_query_cost = (daily_scan_gb / 1024) * 6.25          # on-demand
daily_dml_cost = (daily_scan_gb / 1024) * 6.25 + dml_modified_gb * 0.01
monthly_query_cost = (daily_query_cost + daily_dml_cost) * 30

# --- Streaming ---
events_per_day = 400_000_000
bytes_per_event = 500
stream_gb_per_day = events_per_day * bytes_per_event / 1024**3

free_gb = 1
billable_stream_gb = max(0, stream_gb_per_day - free_gb)
monthly_stream_cost = billable_stream_gb * 30 * (0.01 / 0.2)   # $0.01 per 200 MB

# --- Looker Studio / BI ---
bi_scan_gb_per_day = 200
monthly_bi_cost = (bi_scan_gb_per_day / 1024) * 6.25 * 30

monthly_total = (
    storage_cost + monthly_query_cost + monthly_stream_cost + monthly_bi_cost
)

print(f"Storage:            ${storage_cost:>10,.2f}")
print(f"Batch queries:      ${monthly_query_cost:>10,.2f}")
print(f"Streaming:          ${monthly_stream_cost:>10,.2f}")
print(f"BI / Looker Studio: ${monthly_bi_cost:>10,.2f}")
print(f"{'-' * 34}")
print(f"TOTAL (BigQuery):   ${monthly_total:>10,.2f}")
```

### 5. Break-even analysis: on-demand vs capacity

```python
def breakeven_slot_hours(monthly_on_demand: float, slot_hour_rate: float = 0.04) -> float:
    """Slot-hours per month at which capacity becomes cheaper."""
    return monthly_on_demand / slot_hour_rate


on_demand = 4_200          # $/month from the model above
slots_needed = 100          # baseline
slot_hours = slots_needed * 24 * 30

capacity_cost = slot_hours * 0.04
print(f"On-demand:  ${on_demand:,.2f}")
print(f"Capacity:   ${capacity_cost:,.2f} ({slot_hours:,} slot-hours)")
print(f"Breakeven:  {breakeven_slot_hours(on_demand):,.0f} slot-hours/month")
```

---

## 💡 Production Notes

- **The free tier is per billing account.** Check where your projects sit.
- **Dry run every query.** `total_bytes_processed` is exact and free.
- **Set `maximum_bytes_billed` on every job.** A runaway query should fail, not bill.
- **Long-term storage halves the cost** of cold data — use it for anything older than 30 days
  you still need.
- **Do not move to capacity pricing until on-demand is stable and above ~500 slot-hours/month.**
- **`MERGE` into a partition, never `UPDATE` a whole table.** DML rewrites.
- **`ALTER TABLE ADD COLUMN` on a huge table is not free.** Prefer a new table.
- **Track cost per DAG, per pipeline, and per dashboard.** The billing export gives you
  `labels` and `credits` — use them.
- **Free tier for streaming resets per table per day.** Spread writes across tables only if
  that is genuinely appropriate, not to game the free tier.

---

## 🔑 Key Takeaways

- Four billable dimensions: **storage, query processing, DML, DDL/APIs**.
- On-demand = $6.25 / TiB scanned. **Capacity = slot-hours**, with a commitment.
- Capacity is worth it above roughly 500–1,000 slot-hours/month of stable usage.
- Free tier: 10 GB storage, 1 TiB queries/month, 1 GB/day streaming per table — **per billing
  account**.
- **DML is priced on bytes scanned *and* bytes modified** — it is the most expensive
  operation per row.
- Long-term storage is half price; the move is free.

---

## 📚 Practice Exercises

1. **Cost model for the case study.** Build a spreadsheet-style model for the RetailMart
   pipeline with low/base/high scenarios. Show the sensitivity to event volume, retention, and
   BI usage.

2. **Capacity analysis.** Given an on-demand bill of $6,000/month, model three capacity
   configurations (100, 300, 1,000 slots). Show the crossover point and the risk of idle
   capacity.

3. **Billing export query.** Write a BigQuery SQL query against the GCP billing export that
   produces a weekly cost report by dataset, label, and user agent. Include the DDL to create
   the view.

4. **DML cost comparison.** Compare the cost of: (a) `UPDATE` on a 1 TB non-partitioned table,
   (b) `MERGE` into a date partition, (c) `REPLACE PARTITION`. Include the byte counts.

5. **Quota request.** Write a quota-increase request for a workload that needs 50 TiB/day
   processed, 100k streaming inserts/second, and 500 concurrent queries. Justify each number.

---

## 📖 Further Reading

- BigQuery pricing — https://cloud.google.com/bigquery/pricing
- Reservation overview — https://cloud.google.com/bigquery/docs/reservations-intro
- Quotas and limits — https://cloud.google.com/bigquery/quotas
- GCP billing export schema — https://cloud.google.com/billing/docs/how-to/export-data-bigquery
