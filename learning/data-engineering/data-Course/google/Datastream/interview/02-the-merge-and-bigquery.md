# Module 2 — The Merge & the BigQuery Destination

> **14 questions · Module 2 · The Merge & the BigQuery Destination**

---

## The merge

### 1. What exactly does Datastream do on the BigQuery side of the pipeline?

It applies the change events to the destination table with a **keyed merge** — an upsert-and-delete on a configured merge key.

Concretely, it is equivalent to:

```sql
MERGE `project.dataset.customers` AS target
USING `project.dataset.customers_stream` AS source
    ON target.customer_id = source.customer_id
WHEN NOT MATCHED BY TARGET THEN
    INSERT (customer_id) VALUES (source.customer_id)
WHEN MATCHED AND source.__op__ != 'DELETE' THEN
    UPDATE SET target.customer_id = source.customer_id
WHEN MATCHED AND source.__op__ = 'DELETE' THEN
    DELETE
```

Three clauses, three situations: the key is not in the target, so insert; the key is in the target and the change is not a delete, so update; the key is in the target and the change is a delete, so remove. `__op__` is Datastream's synthetic column recording which operation each event represents — it is not a column in your source table, and it is how one statement handles all three operations.

The distinction that matters to an interviewer: Datastream does not "write events to a table". It **maintains a table**. The destination is a projection of the stream's current state, and the merge is the projection function.

The failure story: a team believed the destination table contained the change history and built an audit report on it. It contained the current state. Every row appeared once with the latest values. The report was wrong for every historical question it was asked, and nobody had a way to answer historical questions from the destination — because the history was in the log, in a different system, which they had not retained.

### 2. What does the merge key have to be, and why?

**The smallest set of columns that uniquely identifies a row in the source table.** Usually the primary key, usually one column. It may be composite — a tenant id plus an id, in a multi-tenant system.

Three properties it must have:

| Property | Why | What breaks without it |
|---|---|---|
| **Unique** | A merge must match exactly one row | One update overwrites several rows |
| **Immutable** | The merge looks rows up by key | A changed key orphans the row |
| **Minimal** | Fewer columns, fewer chances to be wrong | A nullable key component fails to match |

The rule of thumb for the interview: **the source table's primary key**, and nothing else. If the source has no primary key, that is a problem to fix in the source, not something to work around in the merge key.

### 3. What happens if the merge key is not unique?

**One update matches several rows and overwrites all of them. Nothing errors.**

This is the worst failure mode in CDC, because it is silent. The row count does not change. The columns are populated. The table is wrong.

Concretely: merging on `region` when two customers are in EMEA means an update for one of them matches both rows. The second customer's row is overwritten with the first customer's new values.

The detection that works is a **value-level comparison**, not a count:

```python
# Useless — passes with a wrong merge key.
assert len(destination_rows) == len(expected_rows)

# Useless — passes when events are dropped.
assert set(r["customer_id"] for r in destination_rows) == set(
    r["customer_id"] for r in expected_rows
)

# This one catches it.
assert destination_rows == expected_rows
```

The failure story: a pipeline merged on `email`, because email was in every dashboard. A customer changed their email address, which orphaned their old row, and the destination ended up with two rows for one customer. The row count *grew*, so the count check passed. It took a customer complaint — a customer appearing twice in a loyalty calculation — to surface it.

### 4. What happens if the merge key changes value?

**The row is orphaned and a duplicate is created.**

An update that changes the key value has two effects at once: the merge looks up the row by the *new* key, does not find it, and inserts; the old row remains, still keyed on the old value.

So you get two rows for one entity. The row count grows, which is at least a detectable signal, but only if you are watching for growth.

The fix is to merge on an immutable key — the primary key or a surrogate key. Never on an email, a username, a slug, or any other attribute a user can change.

### 5. Why is the merge idempotent, and what does that buy us?

**Every clause of the merge is an upsert or a delete by key. There is no clause that appends.** So applying the same event twice has the same effect as applying it once.

It is a consequence of the shape of the merge, not a configured feature, and it is what makes four routine distributed-systems behaviours safe:

- **Retries** — a failed delivery is redelivered.
- **Replays** — you rebuild the table from the log.
- **Restarts** — the transport restarts mid-stream.
- **Multi-consumer** — two consumers write to the same table.

Without idempotency, every one of those is a corruption event. The signature of a non-idempotent CDC pipeline is a customer table where every customer appears twice, and nobody can say when it started — because it started the first time a consumer retried.

The failure story: a nightly job wrote to BigQuery with `WRITE_APPEND` and used `CURRENT_TIMESTAMP()` for a row's load time. A worker was preempted mid-bundle, the bundle was retried, and the rows landed twice with *different* timestamps. Because the timestamps differed, the downstream `GROUP BY customer_id` double-counted, and the duplicate rows were indistinguishable from two genuine transactions. The fix was a keyed merge with a deterministic row identity.

### 6. What happens on an UPDATE for a row that is not in the destination table?

**Datastream inserts it**, rather than dropping it. The course's implementation does the same.

There are two possible behaviours and the choice matters. If the update were dropped, data would be lost whenever a stream started mid-history and received an update for a row it never saw inserted. Inserting it produces a correct row, because the `after` image *is* the current state of that row.

The cost is that the destination can contain rows the source no longer has, if a delete arrived before the insert and you applied them out of order. That is why stream order matters — it is covered in the ordering question below.

The failure story: a consumer implemented the strict reading and dropped updates for unknown keys. The pipeline looked healthy — no errors, no rejects — and the destination was missing every row that had been updated before the consumer started. The team did not notice for six weeks, because the missing rows were exactly the recently-active customers, and the dashboard they were watching was a monthly report.

### 7. What happens on a DELETE for a row that is not in the destination table?

**Nothing — it is a no-op, not an error.**

This is deliberate and it matters. A stream that starts mid-history will contain deletes for rows it never saw inserted. If the merge treated that as an error, the pipeline would crash on a completely normal situation.

The interesting detail is *why* a delete can identify a row at all: it carries the **before** image. There is no "after" state for a row that no longer exists, so the before image is what tells the merge which key to remove.

This is also why `binlog_row_image = FULL` matters. With `MINIMAL`, the before image contains only the key columns — which is enough to delete, but not enough to tell you *what* was deleted, which breaks audit and backfill.

## Schema and types

### 8. How does Datastream handle a schema change on the source?

Three cases, and the correct response differs for each.

| Case | What happens | Correct response |
|---|---|---|
| **New column** | Destination gains the column; older rows have `NULL` | Accept it. `NULL` is correct. |
| **Dropped column** | New events omit it | Stop reading it; keep or drop the destination column |
| **Changed type** | Events before and after carry different types | Widen, version into a new column, or migrate |

For a new column, the `NULL` in older rows is not a bug — those rows genuinely predate the column, and inventing a value would be a lie that propagates into every downstream average. The exception is a `NOT NULL` column with a default in the source, where the log records the default in the after image.

For a changed type, the pipeline must not decide. A type change handled silently produces a table where old rows are strings and new rows are numbers, and every query that assumes a type fails weeks later in a dashboard nobody remembers building.

### 9. What is the danger of a changed column type mid-stream?

**The stream contains a mix of representations, and a consumer with a fixed schema will either reject the new events or silently coerce them.** Neither is acceptable, because neither is a decision anyone made.

The three defensible responses, with their costs:

- **Widen the destination column.** Correct when the new type is compatible — `INT` to `DECIMAL`. No cost. The column accepts both.
- **New column, keep the old.** Correct when the semantics changed and you want both histories. Costs a migration and a period where the two disagree.
- **A new stream or table.** Correct when the change is breaking and you need a migration window. The most work, and the safest.

The rule for a consumer: **treat every row image as a partial record.** Coerce explicitly, and *count* what you could not read. A rejected value that is counted is a data quality signal. One that raises is an outage. One that is silently dropped is a lie you find in a quarter-end report.

```python
value = row.get("amount")            # not row["amount"]
if value is None:
    rejected += 1
    continue
```

### 10. What are the events Datastream produces, and what is in each?

Three operations — `INSERT`, `UPDATE`, `DELETE` — each carrying a **before** image, an **after** image, and two timestamps.

| Field | Meaning |
|---|---|
| `op` | The operation |
| `before` | The row image before the change. Null for `INSERT`. |
| `after` | The row image after the change. Null for `DELETE`. |
| `sourceTimestamp` | When the **source database** committed the change |
| `serverTimestamp` | When **Datastream** observed the change |

The two timestamps are not the same and the difference is your latency budget. The gap between them is the replication latency, and the gap between `sourceTimestamp` and the merge completing is the end-to-end latency you put in an SLA.

The before image is what makes CDC auditable and what lets a delete identify its row. The after image is what makes an insert and an update produce a row.

## Performance

### 11. Why should the BigQuery destination table be clustered on the merge key?

Because the merge sorts on the merge key before matching, and clustering lets BigQuery **skip the sort and prune blocks**. For a CDC destination this is the single most effective BigQuery optimisation available.

The mechanism: the merge's `ON` clause matches on `customer_id`. With `CLUSTER BY customer_id`, the rows are physically sorted by that column, so BigQuery can restrict the scan to the blocks containing the keys being matched. Without clustering, every merge operation reads the whole table.

The practical effect is that a CDC destination table without clustering gets progressively more expensive as it grows, because each merge touches more rows. A clustered one stays roughly constant.

The numbers: an unclustered CDC destination on a 50-million-row table saw merge costs climb steadily over six months, until the pipeline was the largest line item on the BigQuery bill. Adding `CLUSTER BY customer_id` and partitioning by ingestion date cut the merge cost by roughly an order of magnitude and made it flat.

### 12. Should a CDC destination table be partitioned?

**Yes — partition by the ingestion date.** Two independent reasons.

First, cost. BigQuery's storage is priced per byte, and partitioning lets you expire old partitions with a simple `ALTER TABLE ... DROP PARTITION` rather than a `DELETE` that scans and rewrites.

Second, and more importantly, **merge cost**. A `MERGE` on a partitioned table only touches the partitions it needs. If your destination is partitioned by the date the change was ingested, and you only merge recent changes, you touch a small number of recent partitions rather than the whole history.

The caveat worth knowing: if you partition by ingestion date and the merge matches on a row that was ingested a year ago, the merge must touch that old partition. Some teams partition by the *source's* update timestamp instead, so a row's partition changes as it is updated — but that requires the `WHEN NOT MATCHED` clause to remove the old row, which the streaming merge does not do. Partitioning by ingestion date is the simpler, safer choice.

### 13. How do you monitor a CDC pipeline? What are the metrics that matter?

Four signals, and nothing else:

| Signal | What it tells you |
|---|---|
| **Latency** | How far behind is the destination? |
| **Throughput** | How many events per second are flowing? |
| **Error rate** | Are events being rejected? |
| **Lag** | How much unprocessed change is there? |

**Latency and lag are different**, and confusing them is the classic mistake. Latency is the delay for a single event. Throughput is the rate at which events are processed. If throughput drops below the source's write rate, latency grows without bound — even though every individual event is still processed quickly.

The failure this creates: a stream that looks fine on every dashboard while falling steadily behind. A latency chart showing only recent values displays 2 seconds while the true backlog is four hours.

What does **not** matter: the row count (it goes up and down with churn, and says nothing about health), and the stream state being `READY` (it means the stream has not failed, not that events are flowing).

The alert worth writing is on the **backlog growth rate**, not its size. A backlog that is shrinking is healthy. One growing at 200 events per second is not, even while it is still small.

### 14. How do you cost a CDC pipeline, and what are the levers?

Three cost sources: **Datastream processing**, **BigQuery**, and the **source**.

Datastream charges per GB of change data processed. BigQuery charges for storage, queries, and the DML the merge generates. The source's cost is the binary log volume it generates.

Three levers, in order of impact:

**1. Capture less.** Datastream processes the change data for every table in the source config, including tables you will filter out downstream. Excluding one high-churn audit table at the source can remove 99% of the processing volume. This is the biggest lever and it costs one line of configuration.

**2. Cluster and partition the destination.** As covered above, an unclustered destination's merge cost grows with the table. Clustering on the merge key makes it roughly flat.

**3. Set retention.** On the source side, `binlog_expire_logs_seconds` bounds how much log is retained. On the destination, partition expiration bounds how much is stored.

The cost trap worth naming: because Datastream's cost is per GB of *changes*, a table with high churn is disproportionately expensive to replicate — and that is exactly the case where CDC's operational value is highest, which is an annoying place for the economics and the engineering to disagree.

The failure story: a team replicated eight tables and found the bill was fifteen times their estimate. Seven of the tables were audit and history tables that nobody queried. Excluding them at the source cut the cost by 98%. The lesson was not about cost estimation — it was that the destination config should list the tables you *use*, not the tables you *have*.
