# 6.1 — Operations and Troubleshooting

> **Section 6 · Operations & Recovery · Lecture 6.1 · 28 min**

## 🎯 What you will learn

- How to monitor a Datastream pipeline: the metrics that matter, and the
  ones that do not
- How to tell a **lagging** stream from a **broken** one, and what to do
  about each
- The cost model — what Datastream charges for, and how to keep it bounded
- A 3am triage runbook, in the order to run it
- The four failures you will meet, and the fastest path to each

---

## 🧠 Concept

### What to monitor

Monitoring a CDC pipeline is different from monitoring a batch job. A batch
job either succeeded or failed. A stream is **continuously succeeding at
something**, and the question is always: **is it keeping up?**

There are exactly four things worth watching.

| Signal | What it tells you | Where it comes from |
|---|---|---|
| **Latency** | How far behind is the destination? | `sourceTimestamp` vs the time the merge completed |
| **Throughput** | How many events per second are flowing? | Events applied per minute |
| **Error rate** | Are events being rejected? | Rejects, parse failures, merge failures |
| **Lag** | How much unprocessed change is there? | The log position vs the stream position |

**Latency and lag are not the same.** Latency is the delay for a *single
event* — the time from the source's commit to the merge completing.
Throughput is the *rate* at which events are processed. If throughput
drops below the source's write rate, latency grows without bound, even
though each individual event is still processed quickly.

The failure mode this creates is the one that catches people: **a stream
that looks fine on every dashboard while falling steadily behind.** A
latency chart that only shows recent values will show 2 seconds while the
true backlog is four hours.

### The metrics that do not matter

**Row count.** It goes up, it goes down, it depends on the churn rate.
It tells you nothing about whether the pipeline is healthy.

**"The stream state is READY."** It means the stream is not in a failed
state. It does not mean events are flowing. A stream whose source has
lost its replication privileges can sit in `READY` while ingesting
nothing.

**CPU on the source.** The source should be doing almost nothing. If it
is busy, you are not using CDC properly — you have probably granted too
much privilege and Datastream is reading tables it does not need.

### Triage order

When something is wrong, run these in order. The order matters: each step
narrows the search space, and the later steps are more expensive.

```text
  1. Is the stream RUNNING?          gcloud datastream streams describe
       └─ Not RUNNING ─────────────▶ the error message names the object

  2. Is the stream CONSISTENT?       gcloud datastream streams describe
       └─ Not CONSISTENT ───────────▶ source lag or a schema problem

  3. Is it RUNNING but STALE?        compare sourceTimestamp to now
       └─ Stale ────────────────────▶ the source side: privileges, network,
                                       binary log settings

  4. Is the destination updating?    query the destination table
       └─ Stale but source is fresh ▶ the destination side: merge key,
                                       IAM, quota

  5. Is the data wrong?              compare values against the source
       └─ Wrong ────────────────────▶ the merge key, or a schema change
```

Step 5 is the one people skip, and it is where the answer usually is. A
pipeline that is delivering rows but delivering the *wrong* rows is not a
connectivity problem.

### The cost model

Datastream's charges come from three places:

| What | When you pay | How to bound it |
|---|---|---|
| **Processing** | Per GB of change data processed | Filter tables at the source |
| **BigQuery** | Storage and queries against the destination | Partition and cluster the table |
| **The source** | The log volume it generates | `binlog_row_image`, retention |

The lever that matters most is **how much you capture**. Datastream
processes the change data for every table in its source config, including
tables you will filter out later. Excluding a high-churn audit table at
the source saves both Datastream processing and BigQuery merge cost.

The second lever is the **BigQuery destination's** cost, and it is the one
that surprises people. A CDC destination table that is **not partitioned**
gets more expensive as it grows, because every merge touches more rows. A
table partitioned by ingestion date and clustered on the merge key is
substantially cheaper.

### Recovering from a corrupted destination

The log is the source of truth. Rebuilding is always possible:

```text
  1. Pause the stream.
  2. DROP the destination table.
  3. RECREATE it with the same schema, partitioned and clustered.
  4. Update the stream with --backfill-all.
  5. Resume the stream.
```

The backfill re-copies the current contents and resumes the stream from
the log position. Nothing is lost, because the log still holds everything.

### Recovering from a source-side failure

If the source's binary log has been truncated — because the reader was
disconnected for longer than the retention period — the stream cannot
resume from its old position. The recovery is a full re-backfill, exactly
as above.

This is why Postgres's **replication slots** matter: a slot prevents the
WAL from being truncated past a disconnected reader. The cost is that the
WAL stays on disk, and an unmonitored slot can fill the disk. A slot that
has been inactive for a long time is a common cause of a Postgres
outage.

---

## 🛠️ Hands-On: Diagnosing a Stream

### The triage commands

```bash
# 1. Is it running, and what is the error?
gcloud datastream streams describe main-stream \
    --location=us-central1 \
    --format=json

# 2. The state, without the JSON noise.
gcloud datastream streams describe main-stream \
    --location=us-central1 \
    --format="value(streamState)"

# 3. The per-object state.
gcloud datastream streams describe main-stream \
    --location=us-central1 \
    --format="value(streamState.sourceConfig)"
```

### Model the states

```python
STATES = {
    "READY": "Running normally.",
    "CREATING": "Being set up. Wait.",
    "MIGRATING": "Being reconfigured. Wait — do not cancel.",
    "PAUSED": "Stopped by an operator. Resume it.",
    "FAILED": "Broken. The error message names the object that failed.",
    "RUNNING": "The stream is active but the source is not yet consistent.",
    "NOT_STARTED": "The stream has not begun processing.",
}

for state, meaning in STATES.items():
    print(f"{state:<12} {meaning}")
```

The distinction between `READY` and `RUNNING` is the one people miss.
`RUNNING` means the stream is up but has not reached a consistent state
with the source — typically during the initial backfill, or after a source
failover. It is normal for a while and a problem if it persists.

### Detect a stalled stream

```python
from datetime import datetime, timezone

# The stream's last applied event, and now.
last_applied = datetime(2026, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
now = datetime(2026, 1, 15, 10, 31, 30, tzinfo=timezone.utc)

stalled_for = (now - last_applied).total_seconds()
print(f"stalled for: {stalled_for:.0f}s")

if stalled_for > 300:
    print("STALLED — the stream is up but not delivering.")
    print("Check the source side first: privileges, network, binary log.")
else:
    print("Healthy.")
```

```text
stalled for: 90s
Healthy.
```

### Measure the throughput you need

```python
# The source's write rate, and what the pipeline is keeping up with.
source_rate = 5000          # events per second
pipeline_rate = 4800         # events per second

backlog_growth = source_rate - pipeline_rate
print(f"backlog growth: {backlog_growth:,.0f} events/s")

if backlog_growth > 0:
    hours_to_double = 3_600_000 / backlog_growth / 3600
    print(f"the backlog grows {backlog_growth * 3600:,.0f} events/hour")
    print(f"latency will keep increasing. This pipeline is not keeping up.")
else:
    print("the pipeline is keeping up.")
```

```text
backlog growth: 200 events/s
the backlog grows 720,000 events/hour
latency will keep increasing. This pipeline is not keeping up.
```

This is the calculation that turns "the dashboard looks slow" into an
actionable number. A pipeline running 4% below the source's rate is
**permanently** behind, and no amount of waiting fixes it.

### The cost of capturing too much

```python
# Two tables. One is high-churn and never queried.
TABLES = {
    "customers":    {"events_per_hour": 5_000,   "queried": True},
    "audit_log":    {"events_per_hour": 500_000, "queried": False},
}

total = sum(t["events_per_hour"] for t in TABLES.values())
captured = sum(t["events_per_hour"] for t in TABLES.values() if t["queried"])
excluded = total - captured

print(f"total events/hour      : {total:,}")
print(f"captured if all tables : {captured:,} ({captured / total * 100:.1f}%)")
print(f"saved by excluding the audit log: {excluded:,} ({excluded / total * 100:.1f}%)")
```

```text
total events/hour      : 505,000
captured if all tables : 5,000 (1.0%)
saved by excluding the audit log: 500,000 (99.0%)
```

Excluding one table at the source removes 99% of the processing cost. No
amount of downstream optimisation gets close.

---

## 🛠️ Common Errors and Fixes

### The stream state is `FAILED`

The error message names the failed object. Read it:

```bash
gcloud datastream streams describe main-stream \
    --location=us-central1 \
    --format="value(streamState.status)"
```

Common messages and their fixes:

| Message | Cause | Fix |
|---|---|---|
| `Failed to connect to source host` | Host, port, or firewall | Check the connection profile and the firewall rule |
| `does not have the REPLICATION SLAVE privilege` | Missing grant | `GRANT REPLICATION SLAVE, REPLICATION CLIENT` |
| `binlog_format is not ROW` | Source misconfigured | Set `binlog_format=ROW` and restart |
| `The merge key does not exist in the source table` | Wrong merge key | Fix the destination config |
| `Insufficient permissions to write to BigQuery` | Missing IAM | Grant `roles/bigquery.dataEditor` to the Datastream SA |

### The stream is `READY` but the table is not updating

The stream is up; it is not delivering. Work down the source side:

```bash
# Is the source actually producing changes?
# On the source database:
SHOW BINARY LOGS;
SHOW MASTER STATUS;
```

Then the network, then the privileges, then the binary log settings. The
order is deliberate: the cheapest checks first.

### The stream is `RUNNING` for hours

It is not reaching a consistent state. Usually the backfill is still
running, or the source is a high-write system and the consistency window
cannot keep up. Raise the window, or reduce the backfill's scope.

### BigQuery quota errors

```text
Exceeded rate limits: too many table update operations per second
```

The merge is generating too many DML statements. Batch the changes, or
increase the destination's throughput by clustering on the merge key.

### The destination table is getting expensive

It is not partitioned, so every merge scans more of it. Partition by the
ingestion date, and cluster on the merge key.

### `Could not find a usable replica` / source failover

The source failed over and the replica is in a different zone. The
replication user and the network rules must apply to the new host too. On
Postgres, the replication slot follows the primary automatically — which
is both the reason it prevents data loss and the reason it can hold WAL on
disk.

---

## 💡 Production Notes

- **Alert on lag, not on state.** The stream being `READY` says nothing
  about whether data is flowing.
- **Alert on the *rate* of backlog growth**, not just its size. A backlog
  that is shrinking is healthy; one that grows at 200 events/second is
  not, even though it is currently small.
- **Exclude tables at the source.** It is the single biggest cost lever,
  and it costs one line of configuration.
- **Partition and cluster the destination table.** Partition by ingestion
  date, cluster on the merge key.
- **Reconcile against the source nightly.** A value-level comparison over
  a sample catches everything the metrics miss.
- **Monitor Postgres replication slots.** An inactive slot holds WAL on
  disk and can fill it.
- **Watch the binary log retention.** If the reader is disconnected for
  longer than the retention, the log is truncated and the stream needs a
  full re-backfill.

---

## 🔑 Key Takeaways

- Monitor **lag and throughput**, not row counts and not the stream state.
- **Latency and lag are different.** A pipeline 4% below the source's
  write rate is permanently behind.
- The **triage order** is: running → consistent → stale → delivering →
  correct. Each step narrows the search.
- The **biggest cost lever** is which tables you capture.
- The log is the source of truth — **any corrupted destination can be
  rebuilt** by replaying it.
- Partition and cluster the destination table, or the merge gets
  expensive as it grows.

---

## 📚 Practice Exercises

1. **Write the alert rules.** Write four alerts for a CDC pipeline: one on
   lag, one on the backlog growth rate, one on the error rate, and one on
   the stream state. Give each a threshold and justify it.

2. **Build the triage runbook.** Write the exact `gcloud` commands, in
   order, for the "the stream is READY but the table is stale" case.
   Include the command that shows the last applied event.

3. **Calculate the cost.** Your source writes 10,000 events per second at
   400 bytes each. What is the Datastream processing cost per hour at
   $0.11 per GB? Then calculate the cost if you exclude a table that
   accounts for 90% of the volume.

4. **Design the reconciliation.** Write the SQL that compares the
   destination table against the source, using a sample, and returns only
   the differing rows. Explain why you sample rather than compare
   everything.

5. **Reflection.** The stream has been in `RUNNING` for six hours and the
   backfill is on a 50-million-row table. Write the three options, with
   their trade-offs, for what to do next.

---

## 📖 Further Reading

- Datastream monitoring — https://cloud.google.com/datastream/docs/monitoring
- Datastream troubleshooting — https://cloud.google.com/datastream/docs/troubleshooting
- BigQuery partitioning and clustering — https://cloud.google.com/bigquery/docs/partitioned-tables
- Postgres replication slots — https://www.postgresql.org/docs/current/warm-standby.html#STREAMING-REPLICATION-SLOTS
