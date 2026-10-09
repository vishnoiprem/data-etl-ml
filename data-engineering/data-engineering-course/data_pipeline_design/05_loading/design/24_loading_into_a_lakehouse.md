# 24 — Loading into a Lakehouse (Delta Lake, Iceberg, Hudi)

> **Lesson 24 of 30 — Loading**

The 2026 default for new data architectures. A lakehouse adds
ACID, schema enforcement, and time travel to a Parquet-on-S3
lake. This lesson is what a lakehouse gives you, how to load
into it, and the failure modes that don't exist in a
warehouse.

---

## 1. What a lakehouse adds

A lake is just files on S3. A lakehouse is files on S3 *plus*
a transaction log that records every write.

```
Parquet on S3 (lake):
  /data/events/part-0001.parquet
  /data/events/part-0002.parquet
  + nothing else

Delta on S3 (lakehouse):
  /data/events/part-0001.parquet
  /data/events/part-0002.parquet
  /data/events/_delta_log/000001.json  ← transaction log
  /data/events/_delta_log/000002.json
  + ACID, schema check, time travel
```

The three guarantees:

1. **ACID transactions.** Multi-writer safety. A reader never
   sees a partial write.
2. **Schema enforcement.** Bad data is rejected at write time
   (configurable: `mergeSchema` for additive changes).
3. **Time travel.** Read the table as it was at timestamp T-7.

The senior move: name all three unprompted.

---

## 2. The three lakehouse formats

| Format | Backed by | Strengths |
|---|---|---|
| **Delta Lake** | Databricks | Spark-native, mature, time travel |
| **Apache Iceberg** | Apple, Netflix, Tabular | Hidden partitioning, Hive-compatible |
| **Apache Hudi** | Uber | CDC, record-level updates |

The senior move: "For new architectures I'd default to Delta
on Databricks or Iceberg on Tabular / Snowflake. Hudi is the
right choice if you have heavy CDC workloads with record-level
updates."

---

## 3. The Delta Lake write pattern

The standard write:

```python
from delta.tables import DeltaTable
from pyspark.sql import SparkSession

spark = SparkSession.builder.getOrCreate()
df = spark.read.parquet("s3://staging/events/")

# Write to a Delta table
df.write.format("delta").mode("append").save("s3://data/events/")
```

The modes:
- `append`: add new rows. No checks.
- `overwrite`: replace the entire table or a partition.
- `merge`: upsert on a predicate (the Delta equivalent of
  `MERGE INTO`).

The senior move: "I'd default to `append` for the bronze
layer, `merge` for silver (upsert on event_id), and
`overwrite` for gold (partition overwrite by date)."

---

## 4. The Delta Lake merge pattern

```python
from delta.tables import DeltaTable

delta_table = DeltaTable.forPath(spark, "s3://data/events/")

delta_table.alias("t").merge(
    df.alias("s"),
    "t.event_id = s.event_id"
).whenMatchedUpdateAll().whenNotMatchedInsertAll().execute()
```

This is `MERGE INTO` in Delta syntax. The senior move: "For
silver I'd use Delta's `merge` with `whenMatchedUpdateAll` and
`whenNotMatchedInsertAll`. The semantics match SQL `MERGE INTO`."

---

## 5. The schema enforcement

Delta rejects writes that don't match the table's schema:

```
Write:  { event_id: 1, payload: "x" }   ← existing column
        { event_id: 2, payload: "y", extra: 1 }  ← new column
                                            ↑
                                            rejected (unless mergeSchema)
```

The two settings:
- `mergeSchema=true`: allow new columns, fail on type changes.
- `overwriteSchema=true`: allow any schema change (dangerous).

The senior move: "I'd default to `mergeSchema=true` for the
bronze layer (additive changes are fine) and reject type
changes. For silver and gold I'd reject any schema change
without an explicit migration."

---

## 6. The time travel

Delta can read the table as it was at any point in the past:

```python
# Read the table as of timestamp T-7
df = spark.read.format("delta").option("timestampAsOf", "2024-01-08").load("s3://data/events/")

# Read version 5 of the table
df = spark.read.format("delta").option("versionAsOf", 5).load("s3://data/events/")
```

The benefits:
- **Audit.** "What did the table look like last Tuesday?"
- **Rollback.** "Revert the table to version 5."
- **Reproducibility.** "Re-run the model with the data as of T-7."

The senior move: "I'd keep 30 days of history. After 30 days
I'd run `VACUUM` to delete the old Parquet files."

---

## 7. The compaction (bin-packing)

Delta files accumulate as small files. The `OPTIMIZE` command
compacts them:

```sql
OPTIMIZE delta.`s3://data/events/`
WHERE event_date >= '2024-01-15'
ZORDER BY (user_id);
```

`ZORDER` co-locates rows with similar `user_id` values in the
same file, which speeds up point queries. The senior move: "I'd
run `OPTIMIZE` nightly on the hot partitions. Cold partitions
can wait for weekly."

---

## 8. The vacuum

The `VACUUM` command deletes old files no longer referenced by
the transaction log:

```sql
VACUUM delta.`s3://data/events/` RETAIN 720 HOURS;  -- 30 days
```

Without `VACUUM`, the storage cost grows linearly with the
number of writes. The senior move: "I'd set a 30-day retention
on `VACUUM` and run it weekly."

---

## 9. The Iceberg equivalent

Iceberg has a similar API:

```python
df.write.format("iceberg").mode("append").save("s3://data/events/")

# Time travel
spark.read.format("iceberg").option("snapshot-id", 12345).load("s3://data/events/")
```

The senior move: "If I were on Iceberg instead of Delta, the
patterns are the same. The format choice is mostly
organizational (Databricks vs Snowflake / Tabular)."

---

## 10. The failure modes

| Failure | Mitigation |
|---|---|
| Concurrent writers | ACID transaction log serializes them. |
| Schema change | `mergeSchema=true` for additive; reject type changes. |
| Many small files | `OPTIMIZE` compaction. |
| Storage cost grows | `VACUUM` old files. |
| Wrong data landed | Time travel + `RESTORE` to a prior version. |

The senior move: name the wrong-data failure mode. "If a bad
write corrupts the table, I'd use `RESTORE` to roll back to
the last good version. The transaction log makes this safe."

---

## 11. The interview answer

> "For new architectures I'd default to a lakehouse — Delta
> on Databricks or Iceberg on Snowflake / Tabular. The three
> guarantees are ACID, schema enforcement, and time travel.
> For the bronze layer I'd use `append` with `mergeSchema=true`.
> For silver I'd use `merge` (Delta's `MERGE INTO` equivalent)
> for upsert. For gold I'd use partition overwrite by date.
> I'd run `OPTIMIZE` nightly on hot partitions and `VACUUM`
> weekly with 30-day retention. If a bad write corrupts the
> table, time travel + `RESTORE` is the recovery mechanism."

That single paragraph covers: format choice, three guarantees,
three load modes, compaction, vacuum, recovery. Senior answer
in 30 seconds.

---

## Try it

Look at the most recent lakehouse table you've worked on.
Is it Delta, Iceberg, or Hudi? Is it partitioned by date?
Is `OPTIMIZE` running? Is `VACUUM` running? Is the
retention set? If any is "no," the table will cost 10x more
than it should in 6 months.
