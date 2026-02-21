# Streaming Data with Delta Lake: The Guide I Wish I Had When I Started

*How to build real-time data pipelines that don't break at 3 AM — with code you can copy today*

---

**By [Your Name]** · 15 min read · February 2025

---

Let me tell you about the worst week of my data engineering career.

We had a streaming pipeline ingesting clickstream data from our e-commerce platform. Millions of events per hour. The system worked great — until it didn't.

One random Tuesday, our dashboard showed we'd lost 4 hours of data. Just... gone. The pipeline crashed, and when it restarted, it had no idea where it left off. We had to manually figure out what was missing and backfill it. Three engineers. Two days. Zero sleep.

The root cause? We were writing to plain Parquet files. No transaction guarantees. No reliable checkpointing. No way to recover gracefully.

That's when I discovered Delta Lake.

**Delta Lake solved every problem we had** — and it did it without forcing us to rewrite our entire architecture. Same Spark code, same storage, just... better.

In this guide, I'll show you how streaming with Delta Lake actually works, with real examples you can steal for your own projects.

---

## Why Delta Lake for Streaming? (The 2-Minute Version)

Before we dive in, let me explain why Delta Lake matters for streaming workloads.

Traditional file formats (like Parquet or JSON) have three fatal flaws for streaming:

| Problem | What Happens | Delta Lake Fix |
|---------|--------------|----------------|
| **No transactions** | Partial writes corrupt your data | ACID guarantees on every write |
| **No recovery** | Crash = start over from scratch | Transaction log tracks exactly where you stopped |
| **Small file hell** | Millions of tiny files kill performance | Auto-compaction keeps files optimized |

Here's the thing most tutorials don't tell you: **Delta Lake was literally designed to solve streaming problems.** It started as an internal Databricks project to handle massive streaming ingestion that kept breaking with Parquet.

Now let's see how it works in practice.

---

## The Mental Model: Delta Lake as Both Source AND Sink

Here's the concept that made everything click for me:

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Kafka / Files  │────▶│   Delta Table   │────▶│  Delta Table    │
│  (raw events)   │     │   (Bronze)      │     │  (Silver/Gold)  │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                              │                        │
                         Delta as SINK            Delta as SOURCE
                         (receives data)          (feeds next step)
```

**Delta Lake can be both:**
- A **sink** — where your streaming data lands
- A **source** — where your next processing step reads from

This is huge. It means you can chain streaming processes together without needing Kafka in the middle. Your "Bronze" table receives raw data, your "Silver" table reads from Bronze as a stream, and your "Gold" table reads from Silver.

One format. Multiple streaming stages. No infrastructure juggling.

---

## Streaming vs. Batch: What's the Real Difference?

I used to think streaming and batch were completely different beasts. They're not.

**The only real difference is latency.**

Think of it this way:

```
BATCH PROCESSING
────────────────────────────────────────────────────────
Files arrive → Wait for schedule → Process all at once
              (e.g., midnight)    (big batch)

STREAMING PROCESSING  
────────────────────────────────────────────────────────
Files arrive → Process immediately → Continuous output
              (as each arrives)     (small batches)
```

The business logic? Usually identical. The code? Almost the same. The difference is *when* and *how often* you run it.

This is why frameworks like Spark have a "unified API" — you write similar code for both. And Delta Lake works seamlessly with either approach.

---

## Real Example #1: E-Commerce Clickstream Pipeline

Let's build something real. We'll create a streaming pipeline that:
1. Ingests raw clickstream events
2. Cleans and enriches the data
3. Creates real-time aggregations for dashboards

### The Bronze Layer: Raw Ingestion

First, let's ingest events from a file source (this could be Kafka too):

```python
# Read streaming events from source
raw_events = (
    spark
    .readStream
    .format("json")
    .schema(event_schema)
    .load("/data/incoming/clickstream/")
)

# Write to Delta Lake (Bronze layer)
(raw_events
    .writeStream
    .format("delta")
    .outputMode("append")
    .option("checkpointLocation", "/checkpoints/bronze_clickstream")
    .start("/delta/bronze/clickstream")
)
```

**What's happening here:**
- `readStream` creates a streaming DataFrame
- `writeStream` with `format("delta")` writes to a Delta table
- `checkpointLocation` is where Delta tracks progress

**The magic:** If this crashes and restarts, it picks up exactly where it left off. No data loss. No duplicates. That's what saved us from the disaster I mentioned.

### The Silver Layer: Delta as Source

Now here's where it gets cool. We can read from that Delta table as a streaming source:

```python
# Read from Bronze as a stream
bronze_stream = (
    spark
    .readStream
    .format("delta")
    .load("/delta/bronze/clickstream")
)

# Clean and transform
silver_stream = (
    bronze_stream
    .filter(col("event_type").isNotNull())
    .filter(col("user_id").isNotNull())
    .withColumn("event_date", to_date("event_timestamp"))
    .withColumn("processed_at", current_timestamp())
)

# Write to Silver layer
(silver_stream
    .writeStream
    .format("delta")
    .outputMode("append")
    .option("checkpointLocation", "/checkpoints/silver_clickstream")
    .start("/delta/silver/clickstream")
)
```

**The magic:** Delta Lake automatically tracks which records have been processed. New data in Bronze automatically flows to Silver. It feels like magic, but it's actually just good engineering.

### The Gold Layer: Real-Time Aggregations

Finally, let's create a real-time dashboard table:

```python
# Read from Silver
silver_events = (
    spark
    .readStream
    .format("delta")
    .load("/delta/silver/clickstream")
)

# Aggregate by product and hour
hourly_metrics = (
    silver_events
    .withWatermark("event_timestamp", "1 hour")
    .groupBy(
        window("event_timestamp", "1 hour"),
        "product_id"
    )
    .agg(
        count("*").alias("view_count"),
        countDistinct("user_id").alias("unique_users"),
        sum("revenue").alias("total_revenue")
    )
)

# Write to Gold layer
(hourly_metrics
    .writeStream
    .format("delta")
    .outputMode("complete")
    .option("checkpointLocation", "/checkpoints/gold_metrics")
    .start("/delta/gold/hourly_product_metrics")
)
```

**Result:** A real-time dashboard that updates continuously as events flow in. Your business team sees metrics within minutes, not hours.

---

## Real Example #2: Banking Transaction Monitoring

Let's say you're building a fraud detection system. You need to:
- Ingest transactions in real-time
- Join with customer data
- Flag suspicious patterns

### The Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Transaction    │────▶│   Enriched      │────▶│  Fraud Alerts   │
│  Events (Kafka) │     │   Transactions  │     │  (Dashboard)    │
└─────────────────┘     └─────────────────┘     └─────────────────┘
        │                       │                       │
   Real-time              Join with                Rules engine
   ingestion             customer data            + aggregations
```

### Step 1: Ingest from Kafka to Delta

```python
# Stream transactions from Kafka
transactions = (
    spark
    .readStream
    .format("kafka")
    .option("kafka.bootstrap.servers", "broker:9092")
    .option("subscribe", "transactions")
    .load()
    .select(from_json(col("value").cast("string"), tx_schema).alias("tx"))
    .select("tx.*")
)

# Write to Delta Bronze (with exactly-once semantics)
(transactions
    .writeStream
    .format("delta")
    .outputMode("append")
    .option("checkpointLocation", "/checkpoints/transactions_bronze")
    .start("/delta/bronze/transactions")
)
```

### Step 2: Enrich with Customer Data

Now the interesting part — joining streaming data with a static customer table:

```python
# Read transactions as stream
tx_stream = (
    spark
    .readStream
    .format("delta")
    .load("/delta/bronze/transactions")
)

# Read customer data (static lookup table)
customers = spark.read.format("delta").load("/delta/dim/customers")

# Enrich transactions with customer info
enriched = (
    tx_stream
    .join(customers, "customer_id", "left")
    .select(
        tx_stream["*"],
        customers["risk_score"],
        customers["account_age_days"],
        customers["avg_transaction_amount"]
    )
)

# Flag suspicious transactions
flagged = (
    enriched
    .withColumn("is_suspicious", 
        when(
            (col("amount") > col("avg_transaction_amount") * 5) |
            (col("risk_score") > 0.8) |
            ((col("account_age_days") < 30) & (col("amount") > 1000)),
            True
        ).otherwise(False)
    )
)

# Write to Silver
(flagged
    .writeStream
    .format("delta")
    .outputMode("append")
    .option("checkpointLocation", "/checkpoints/transactions_silver")
    .start("/delta/silver/transactions")
)
```

**Why this matters for banking:**
- Every transaction is tracked (audit trail built-in)
- If the system crashes, no transactions are lost or duplicated
- You can time-travel to see data at any point (regulatory compliance)
- Real-time fraud alerts without complex infrastructure

---

## The Streaming Options That Actually Matter

Delta Lake has lots of options. These are the ones I actually use:

### 1. Rate Limiting: Don't Overwhelm Your Cluster

```python
# Limit files per batch
spark.readStream
    .format("delta")
    .option("maxFilesPerTrigger", 100)  # Process max 100 files per batch
    .load("/delta/source")

# Or limit by size
spark.readStream
    .format("delta")
    .option("maxBytesPerTrigger", "10g")  # Process ~10GB per batch
    .load("/delta/source")
```

**When to use:** Your source table is huge, and you don't want to process everything at once. Great for:
- Backfill scenarios
- Cost control
- Preventing cluster overload

### 2. Handling Updates and Deletes

By default, Delta Lake streaming assumes append-only. If someone updates or deletes data upstream, your stream will fail.

```python
# Ignore deletes (useful for GDPR compliance)
spark.readStream
    .format("delta")
    .option("ignoreDeletes", "true")
    .load("/delta/source")

# Treat changes as new records
spark.readStream
    .format("delta")
    .option("ignoreChanges", "true")
    .load("/delta/source")
```

**Real scenario:** You have a GDPR delete request. You delete the user's data from the source table. With `ignoreDeletes`, your downstream pipeline continues without failing — you just need to run the same delete downstream separately.

**Important difference:**
- `ignoreDeletes` = Skip delete operations entirely
- `ignoreChanges` = Treat updated/deleted records as new inserts (you'll need deduplication logic downstream)

### 3. Starting from a Specific Point

Don't want to reprocess everything from the beginning?

```python
# Start from a specific version
spark.readStream
    .format("delta")
    .option("startingVersion", 125)
    .load("/delta/source")

# Or from a specific timestamp
spark.readStream
    .format("delta")
    .option("startingTimestamp", "2024-01-15")
    .load("/delta/source")
```

**When to use:** 
- Setting up a new downstream table from a specific point
- Recovering from a failed pipeline
- Testing with recent data only

---

## The Medallion Architecture in Practice

This pattern comes up constantly. Here's how it actually works end-to-end:

```
┌──────────────────────────────────────────────────────────────────────┐
│                        MEDALLION ARCHITECTURE                        │
├──────────────────┬───────────────────┬───────────────────────────────┤
│      BRONZE      │       SILVER      │             GOLD              │
├──────────────────┼───────────────────┼───────────────────────────────┤
│ Raw data         │ Cleaned data      │ Aggregated data               │
│ As-is from source│ Validated         │ Business-ready                │
│ Schema-on-read   │ Schema enforced   │ Optimized for queries         │
│ Append-only      │ Deduplicated      │ Pre-computed metrics          │
└──────────────────┴───────────────────┴───────────────────────────────┘
```

### Complete Pipeline Code

```python
# ============================================
# BRONZE: Raw ingestion (from files)
# ============================================
bronze_stream = (
    spark.readStream
    .format("cloudFiles")  # Auto Loader on Databricks
    .option("cloudFiles.format", "json")
    .option("cloudFiles.schemaLocation", "/schemas/orders")
    .load("/data/incoming/orders/")
)

bronze_write = (
    bronze_stream
    .writeStream
    .format("delta")
    .outputMode("append")
    .option("checkpointLocation", "/checkpoints/orders_bronze")
    .trigger(processingTime="1 minute")
    .start("/delta/bronze/orders")
)

# ============================================
# SILVER: Cleaned and validated
# ============================================
silver_source = (
    spark.readStream
    .format("delta")
    .load("/delta/bronze/orders")
)

silver_cleaned = (
    silver_source
    .filter(col("order_id").isNotNull())
    .filter(col("amount") > 0)
    .dropDuplicates(["order_id"])
    .withColumn("order_date", to_date("order_timestamp"))
)

silver_write = (
    silver_cleaned
    .writeStream
    .format("delta")
    .outputMode("append")
    .option("checkpointLocation", "/checkpoints/orders_silver")
    .trigger(processingTime="1 minute")
    .start("/delta/silver/orders")
)

# ============================================
# GOLD: Business aggregations
# ============================================
gold_source = (
    spark.readStream
    .format("delta")
    .load("/delta/silver/orders")
)

daily_summary = (
    gold_source
    .withWatermark("order_timestamp", "1 day")
    .groupBy(
        window("order_timestamp", "1 day"),
        "product_category"
    )
    .agg(
        count("order_id").alias("order_count"),
        sum("amount").alias("total_revenue"),
        avg("amount").alias("avg_order_value")
    )
)

gold_write = (
    daily_summary
    .writeStream
    .format("delta")
    .outputMode("complete")
    .option("checkpointLocation", "/checkpoints/orders_gold")
    .trigger(processingTime="5 minutes")
    .start("/delta/gold/daily_sales")
)
```

**What's beautiful about this:**
- Each layer is independent (if Silver fails, Bronze keeps running)
- If you need to reprocess Silver, Bronze data is still there
- Clear separation of concerns
- Easy to debug (check each layer separately)

---

## Change Data Feed: Track Every Change

Want to know exactly what changed in your table? Enable Change Data Feed:

```sql
-- Enable on a new table
CREATE TABLE customers (
    customer_id STRING,
    name STRING,
    email STRING
)
USING DELTA
TBLPROPERTIES (delta.enableChangeDataFeed = true);

-- Or enable on existing table
ALTER TABLE customers 
SET TBLPROPERTIES (delta.enableChangeDataFeed = true);
```

Now you can read changes as a stream:

```python
# Read only the changes
changes = (
    spark.readStream
    .format("delta")
    .option("readChangeFeed", "true")
    .option("startingVersion", 0)
    .table("customers")
)

# See what changed
changes.select(
    "customer_id",
    "name",
    "_change_type",      # insert, update_preimage, update_postimage, delete
    "_commit_version",
    "_commit_timestamp"
).show()
```

**Output looks like:**

| customer_id | name | _change_type | _commit_version |
|-------------|------|--------------|-----------------|
| C001 | John | insert | 1 |
| C001 | John Doe | update_preimage | 3 |
| C001 | John Smith | update_postimage | 3 |

**Real use cases:**
- **Audit trails:** Who changed what, when?
- **Sync to other systems:** Send only changes to downstream databases
- **CDC pipelines:** Build change data capture without Debezium

---

## Handling Upserts in Streaming (foreachBatch)

Sometimes you need to update existing records, not just append. Here's how:

```python
from delta.tables import DeltaTable

def upsert_to_delta(batch_df, batch_id):
    """Merge streaming batch into target table"""
    
    target_table = DeltaTable.forPath(spark, "/delta/silver/customers")
    
    (target_table.alias("target")
        .merge(
            source=batch_df.alias("source"),
            condition="source.customer_id = target.customer_id"
        )
        .whenMatchedUpdate(set={
            "name": "source.name",
            "email": "source.email",
            "updated_at": "source.updated_at"
        })
        .whenNotMatchedInsert(values={
            "customer_id": "source.customer_id",
            "name": "source.name",
            "email": "source.email",
            "updated_at": "source.updated_at"
        })
        .execute()
    )

# Apply to streaming DataFrame
(customer_updates_stream
    .writeStream
    .foreachBatch(upsert_to_delta)
    .option("checkpointLocation", "/checkpoints/customer_upserts")
    .start()
)
```

**When to use:**
- CDC record processing
- Dimension table updates
- Any scenario where you need UPSERT (update or insert)

---

## Common Pitfalls (And How to Avoid Them)

### Pitfall #1: Forgetting the Checkpoint Location

```python
# ❌ BAD - No checkpoint
stream.writeStream.format("delta").start("/delta/table")

# ✅ GOOD - Always include checkpoint
stream.writeStream
    .format("delta")
    .option("checkpointLocation", "/checkpoints/my_stream")
    .start("/delta/table")
```

**Why it matters:** Without checkpoints, crashes mean starting over. Every. Single. Time.

### Pitfall #2: Vacuum Deleting Data Your Stream Needs

```python
# ❌ DANGEROUS - Might delete files your stream needs
spark.sql("VACUUM my_table RETAIN 0 HOURS")

# ✅ SAFE - Keep enough history
spark.sql("VACUUM my_table RETAIN 168 HOURS")  # 7 days
```

**Rule of thumb:** Keep retention longer than your longest possible stream restart time.

### Pitfall #3: Schema Changes Breaking Streams

```python
# ✅ Allow schema evolution
stream.writeStream
    .format("delta")
    .option("mergeSchema", "true")
    .start("/delta/table")
```

### Pitfall #4: Not Monitoring Your Streams

Always check these metrics:
- `inputRowsPerSecond` — How fast data is arriving
- `processedRowsPerSecond` — How fast you're processing
- `numFilesOutstanding` — Backlog of unprocessed files

**If input > processed:** You're falling behind. Add more resources or reduce trigger frequency.

---

## Quick Reference: Streaming Options Cheat Sheet

| Option               | What It Does                | Default   | Example        |
|----------------------|-----------------------------|-----------|----------------|
| `maxFilesPerTrigger` | Limit files per batch       | 1000      | `100`          |
| `maxBytesPerTrigger` | Limit data per batch        | None      | `"10g"`        |
| `ignoreDeletes`      | Skip delete operations      | false     | `"true"`       |
| `ignoreChanges`      | Treat changes as inserts    | false     | `"true"`       |
| `startingVersion`    | Start from specific version | 0         | `125`          |
| `startingTimestamp`  | Start from specific time    | None      | `"2024-01-15"` |
| `readChangeFeed`     | Read change data feed       | false     | `"true"`       |

---

## The Bottom Line

Delta Lake turns streaming from "hope it works" to "know it works."

**The three things that changed my career:**

1. **Checkpointing** — Never lose track of progress again
2. **ACID transactions** — No more corrupt data from partial writes  
3. **Unified batch and streaming** — Same code works for both

**My advice for getting started:**

1. Start with the medallion architecture (Bronze → Silver → Gold)
2. Always set checkpoint locations
3. Use `ignoreDeletes` if you have GDPR requirements
4. Monitor your metrics (input vs. processed rows)
5. Keep vacuum retention > longest stream restart time

The best streaming pipeline is the one you don't have to think about at 3 AM.

---

## Further Reading

- [Delta Lake Documentation](https://delta.io)
- *Learning Spark* by Jules Damji et al. (O'Reilly)
- *Fundamentals of Data Engineering* by Joe Reis & Matt Housley

---

*Found this useful? Follow for more practical data engineering guides that actually make sense.*

---

*Originally published on Medium*
