# Module 3 — Operations, Schema & Recovery

> **14 questions · Module 3 · Operations, Schema & Recovery**

---

## Backfill and recovery

### 1. What is a backfill in Datastream, and when do you want one?

A backfill copies the **existing contents** of the source table into the destination before the stream starts delivering changes.

You want `--backfill-all` in almost every case. Without it, the destination starts empty and fills up only with changes that happen *after* the stream starts — so every row that existed before is missing. The table looks like it is working; it is just missing almost all of the data.

The three modes:

| Mode | Behaviour | When |
|---|---|---|
| `backfill-all` | Copy the contents, then stream changes | **The default choice.** |
| `backfill-none` | Stream changes only, from now | The destination already has the data, or the table is genuinely empty. |
| `backfill-config` | Copy the contents, with a filter and column mapping | The source has columns you do not want, or you are backfilling a subset. |

The critical detail is the **coordination** between the backfill and the stream. The backfill takes a snapshot at a point in the log; the stream resumes from exactly that point. Everything before the snapshot is in the backfill, everything after it is in the stream. Nothing is lost and nothing is applied twice.

### 2. Why must the destination table be empty before a backfill?

**Because the backfill's snapshot and the existing rows will conflict, and the merge cannot resolve it.** The merge has no way to know which copy of a row is correct — it has no version information and no timestamp comparison.

The result is duplicates that persist, and the only fix is to drop and recreate the table and backfill again.

This is the one procedure where there is no shortcut, and it is worth stating that plainly in an interview, because "can we just backfill into the existing table?" is a question that always gets asked.

The recovery sequence, when it goes wrong:

```text
  1. Pause the stream.
  2. DROP TABLE `PROJECT.dataset.customers`;
  3. Recreate it with the same schema, partitioned and clustered.
  4. Update the stream with --backfill-all.
  5. Resume the stream.
```

### 3. The destination table is corrupted. How do you recover?

**Replay the log.** The binary log is the source of truth for what changed, so a corrupted destination is always rebuildable.

```text
  1. Pause the stream.        (so nothing new arrives mid-rebuild)
  2. DROP the destination table.
  3. RECREATE it with the same schema.
  4. Update the stream with --backfill-all.
  5. Resume the stream.
```

The backfill re-copies the current table contents and resumes the stream from the log position. Nothing is lost, because the log still holds everything.

The window while the stream is paused is safe — changes during it are in the log and the stream resumes from where it left off.

The alternative recovery, when you need the *history* rather than the current state, is to read the change events directly and rebuild both the table and an audit trail. That is what a log-based warehouse does, and it is a different design.

### 4. The source's binary log was truncated. What now?

**A full re-backfill**, exactly as above. The stream cannot resume from a log position that no longer exists.

This is a real risk and it has a specific cause: the reader was disconnected for longer than the log retention period. On MySQL, `binlog_expire_logs_seconds` bounds retention. On Postgres, the equivalent protection is a **replication slot**, which prevents the WAL from being truncated past a disconnected reader.

The Postgres slot is a double-edged tool, and this is worth knowing for the interview: the slot prevents data loss, but it also holds WAL on disk indefinitely while the reader is down. An unmonitored, long-inactive slot can fill the disk and take Postgres down. A common operational finding is a slot that has been inactive for weeks, holding several gigabytes of WAL for a consumer that no longer exists.

### 5. How do you handle a source schema change that breaks the pipeline?

In order:

**1. Decide, before touching the pipeline, which of the three responses applies** — widen, version, or migrate. The pipeline must not decide.

**2. Widen the destination column** if the change is compatible:

```sql
ALTER TABLE `PROJECT.dataset.customers`
ALTER COLUMN amount TYPE NUMERIC;
```

**3. If the change is breaking, create a new column or a new table** and let the old one stay for historical queries.

**4. Update the destination config** with the new column mapping if the column set genuinely changed.

**5. Add a migration window.** If the change is breaking and you cannot migrate atomically, run the old and new streams into two tables, backfill the new one, cut over the reads, and drop the old one later.

The failure story that makes the point: a team added a `status` column as a string in the source, then changed it to an integer. The pipeline coerced the values, because the destination column was `STRING` and the consumer called `str()`. For six months the destination held `"1"`, `"2"`, `"3"` as strings, and every numeric aggregation silently returned zero. It surfaced when a finance report showed revenue of 0 for a category that had never been zero.

## Operations

### 6. How do you tell a lagging stream from a broken one?

**A broken stream has an error message and a non-READY state. A lagging stream is READY and delivering, just not fast enough.** They need completely different responses, and the mistake is treating a lag problem as a connectivity problem.

The test is arithmetic, not observational:

```text
  backlog growth = source write rate − pipeline processing rate
```

If the growth rate is positive, the pipeline is permanently behind — no amount of waiting fixes it. A pipeline running 4% below the source's rate falls behind forever. If the growth rate is zero, it is keeping up. If it is negative, it is catching up.

The source write rate is measurable: count the transactions per second on the source database. The processing rate is the number of events applied per minute, which the stream's metrics give you.

The failure story: a team treated a lag problem as a connectivity problem for a week. They were restarting the stream, checking the firewall, re-granting privileges, and rebuilding the destination. None of it helped, because the pipeline was working perfectly — it was just configured with a merge key that made each operation take ten times longer than necessary. The backlog was growing because throughput was 10% of the source's rate. The fix was one config change.

### 7. The stream is `READY` but the destination table is not updating. What do you check?

Work down the source side, cheapest checks first:

**1. Is the source producing changes at all?**

```sql
SHOW BINARY LOGS;
SHOW MASTER STATUS;
```

If the log position is not advancing, the problem is upstream of Datastream entirely.

**2. Are the privileges still correct?**

```sql
SHOW GRANTS FOR 'datastream_user'@'%';
```

A password expiry on the replication user presents exactly like this: the stream stays `READY`, the connection profile is valid, and nothing arrives.

**3. Is the binary log configured correctly?**

```sql
SHOW VARIABLES LIKE 'binlog_format';
SHOW VARIABLES LIKE 'binlog_row_image';
```

**4. Is the firewall open to the Datastream IP allocation?**

```bash
gcloud datastream network-configs ip-pools list \
    --location=us-central1 --network-config=network-config
```

Compare that address against the source's firewall rules. A timeout rather than a refusal points here.

**5. Is the source config capturing the tables you expect?**

```bash
gcloud datastream source-configs describe mysql-source \
    --location=us-central1 \
    --format="value(mysqlSourceConfig.includeTables)"
```

Then, if the source is definitely producing changes and they are definitely not arriving, check the destination side: the merge key, the Datastream service account's BigQuery IAM, and the project's BigQuery quotas.

### 8. What does the `RUNNING` state mean, and is it a problem?

**The stream is up but has not yet reached a consistent state with the source.** It is normal during the initial backfill and after a source failover, and it is a problem if it persists.

During a backfill, the stream is consuming the table's history, which can take a long time on a large table. That is expected `RUNNING` behaviour, not a failure.

After a failover, the new primary has a different log position, and the stream has to re-establish its position. That can involve a re-backfill if the position is unrecoverable.

The concerning case is `RUNNING` with no backfill in progress, which usually means the read consistency window cannot keep up with the write load, or the source has a networking problem that prevents the consistency check from completing.

### 9. What is the difference between latency and lag, and why do you need both?

**Latency** is the delay for a single event — the time from the source's commit to the merge completing. **Lag** is the total amount of unprocessed change sitting between the source's current position and the stream's position.

They are related but not the same, and conflating them causes missed incidents.

A pipeline can have low latency and high lag: it processes each event quickly, but it is not processing them fast enough to catch up. The backlog grows while every individual event looks fine.

A pipeline can have high latency and low lag: it is caught up, but each event took a long time. That is usually one slow merge batch.

You need both because they have different causes and different fixes. High latency with low lag is a merge performance problem. Low latency with growing lag is a throughput problem. And a dashboard showing only recent latency values will show 2 seconds while the backlog is four hours old.

### 10. How do you know the pipeline is delivering *correct* data, not just data?

**Reconcile the destination against the source, comparing values.** The comparison is the whole point — a count check passes with a wrong merge key.

```sql
WITH source AS (SELECT * FROM `PROJECT.reconciliation.customers_source_snapshot`),
destination AS (SELECT * FROM `PROJECT.datastream.customers`)

SELECT 'MISSING' AS discrepancy, s.customer_id
FROM source s LEFT JOIN destination d USING (customer_id)
WHERE d.customer_id IS NULL

UNION ALL

SELECT 'EXTRA', d.customer_id
FROM destination d LEFT JOIN source s USING (customer_id)
WHERE s.customer_id IS NULL

UNION ALL

SELECT 'VALUE_MISMATCH', s.customer_id
FROM source s JOIN destination d USING (customer_id)
WHERE s.tier IS DISTINCT FROM d.tier
   OR s.region IS DISTINCT FROM d.region;
```

Three categories, and each maps to a distinct root cause: **MISSING** means inserts were dropped or the backfill did not cover the table. **EXTRA** means deletes were not applied. **VALUE_MISMATCH** means a wrong merge key or a dropped update.

Run it on a **sample** nightly. A full comparison on a large table is expensive; a random 10,000-row sample catches a systematic problem immediately and a rare one eventually.

The most important subtlety: **reconcile against the source, not against the stream.** Comparing the destination to a reconstruction from the stream only proves the merge works. Comparing it to the source proves the *pipeline* works. If you reconstruct the expected table from the same events you fed the destination, a pipeline that captured the wrong table entirely will still reconcile perfectly.

## Ordering and consistency

### 11. Does Datastream preserve the order of changes?

**Yes — within a single source, Datastream delivers changes in the order the source committed them.** That is why the merge converges: an update always arrives after its insert, and a delete after the update that preceded it.

The ordering guarantee comes from reading the log sequentially. It is one of the strongest properties of the Datastream path, and it is what makes the keyed merge sufficient.

The exception is when you fan a CDC stream out through Kafka. **Kafka guarantees ordering within a partition and nothing across partitions.** So the Kafka partitioning key must be the same key you merge on. If you partition by something else, updates for one row can arrive out of order and the merge converges on the wrong value.

This is not a coincidence — it is the requirement that makes a partitioned stream mergeable at all.

### 12. What does the merge do with a DELETE that arrives before its INSERT?

**Delete-then-insert leaves the row. Insert-then-delete removes it.**

The merge is order-sensitive for the delete/insert pair on the same key, and it must be: these are genuinely different outcomes and there is no merge that could treat them the same without being wrong.

In a well-behaved CDC stream this does not happen, because the log preserves commit order and a row cannot be deleted before it was inserted — within a transaction. But it happens in three real situations:

- **A stream that starts mid-history**, where the first event for a key is an update or a delete.
- **A Kafka fan-out** where the partitioning key does not match the merge key.
- **Multiple source databases** feeding one destination, where there is no global order at all.

For the first case the answer is the upsert behaviour — an update for an unknown key inserts the row rather than dropping it, so no data is lost. For the second, the fix is to partition by the merge key. For the third, the answer is that you need a global ordering mechanism, and most designs do not have one.

### 13. What is the `__op__` column and why does it matter?

**It is Datastream's synthetic column recording which operation each change event represents**, and it is what lets a single `MERGE` statement handle all three operations.

```sql
WHEN MATCHED AND source.__op__ != 'DELETE' THEN UPDATE ...
WHEN MATCHED AND source.__op__ = 'DELETE'   THEN DELETE ...
```

It is not a column in your source table. If your source happens to have a column called `__op__`, it is a name collision, and you should rename it — the reserved prefix is there precisely to avoid colliding with real columns, but a source column with a leading double underscore is bad practice regardless.

The failure story: a custom consumer did not use `__op__` and instead inferred the operation from which image was null. That works for `INSERT` and `DELETE`, but it cannot distinguish an `UPDATE` from an `INSERT` — both have a non-null `after` image. Every update was applied as an insert, and the destination table became a growing multiset. The fix was to read the operation from the event rather than inferring it from the payload.

### 14. What causes a BigQuery "too many table update operations" error, and how do you fix it?

**The merge is generating more DML statements per second than BigQuery's per-table update quota allows.** The quota is on concurrent DML operations against a single table, and a high-throughput CDC stream can exceed it.

The fixes, in order of preference:

**1. Batch the changes.** Group the events into fewer, larger merge statements rather than one per event. This is the real fix — a merge of 1,000 changes costs far less than 1,000 merges of one change.

**2. Cluster on the merge key.** A clustered table lets BigQuery prune blocks and skip the sort, which reduces the time each merge holds its quota slot.

**3. Raise the quota.** Available on some projects, and it treats the symptom.

**4. Partition by ingestion date.** A merge that only touches recent partitions is faster and holds its slot for less time.

The failure story: a pipeline moving 8,000 events per second hit the quota constantly, and the standard advice was to raise the quota. Raising it made the pipeline faster and it hit a *different* limit — BigQuery's DML statement rate — which manifested as a much harder-to-diagnose partial-failure pattern where some events were applied and others silently dropped by the merge's own error handling. The actual fix was batching, which reduced the DML rate by three orders of magnitude.
