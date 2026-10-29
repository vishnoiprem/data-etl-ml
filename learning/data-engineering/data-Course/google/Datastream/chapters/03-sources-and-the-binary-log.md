# 3.1 — Sources and the Binary Log

> **Section 3 · Configuring the Source · Lecture 3.1 · 30 min**

## 🎯 What you will learn

- How a database's write-ahead log works, and why CDC reads it instead of
  the tables
- The four source types Datastream supports, and which one you are likely
  to use
- The MySQL and Postgres prerequisites — `binlog_format=ROW`,
  `binlog_row_image=FULL`, and the replication privileges
- The **read consistency window**: what it does, what it costs, and how to
  choose it
- The network path from Datastream to your source database

---

## 🧠 Concept

### Why the log, and not the tables

Every database that supports CDC has a **write-ahead log** — a durable,
ordered, append-only record of every change it commits. The log exists so
that the database can recover after a crash: replay the log onto the last
checkpoint and you have the state back.

CDC exploits this. Instead of reading the tables, you read the log.

That choice is what makes CDC cheap, and it is worth understanding exactly
why:

| | Reading tables (polling) | Reading the log (CDC) |
|---|---|---|
| Access pattern | Random — index probe, then row fetch | **Sequential** — read the next entry |
| Load on the source | CPU and buffer cache pressure on the hot data | Minimal — the log is written anyway |
| Sees deletes | No | **Yes** |
| Sees transactions | No — sees rows half-updated | **Yes** — the transaction boundary is in the log |
| Replayable | No | **Yes** |

The last two rows are the ones that matter, and neither is about
performance.

**Seeing transactions** is the subtle one. A polling query that reads rows
where `updated_at > last_run` might catch a 500-row transaction with 300
rows already updated and 200 not yet. Your table now has a half-applied
transaction — an order with line items but no header, say. A log-based
reader sees the transaction commit atomically, because the log records the
commit as a unit.

**Replayability** is what makes recovery possible. If the destination
table is corrupted, you replay the log from a known-good point and rebuild
it. With polling, there is no such thing — you have no record of what
changed, only what is true now.

### Logical vs physical decoding

Datastream reads the **logical** form of the log — the actual row changes —
not the physical pages that were written. The distinction matters:

- **Statement-based** (`binlog_format=STATEMENT`) records the SQL. A
  multi-row statement becomes one ambiguous event, and you cannot tell what
  each row became. **CDC cannot use this.**
- **Row-based** (`binlog_format=ROW`) records the row images. One event per
  row changed, with before and after images. **This is what CDC needs.**
- **Mixed** (`binlog_format=MIXED`) uses statement format except for
  unsafe statements. Avoid it.

### The row image setting

```ini
binlog_format = ROW
binlog_row_image = FULL
```

`binlog_row_image` controls how much of the row is recorded:

| Setting | What is logged | CDC consequence |
|---|---|---|
| `FULL` | Every column, before and after | Complete images. Backfills work. Audits work. |
| `MINIMAL` | Only the changed columns and the key | Faster, smaller — but **before images are incomplete** |
| `NOBLOB` | All columns except large blobs | A middle ground |

`MINIMAL` is tempting because it reduces log volume by a lot on wide tables.
It breaks things. A `before` image that only has the key means you cannot
tell what the row used to contain — so you cannot reconstruct history, and
a delete event cannot tell you what was deleted.

For CDC, use `FULL`. The performance argument is real but the correctness
argument is stronger.

### The four source types

| Source | Notes |
|---|---|
| **MySQL** | The most common. Requires `binlog_format=ROW` and a replication user. |
| **PostgreSQL** | Requires `wal_level=logical`. Supports **logical replication slots**. |
| **Oracle** | Uses the redo log. Requires specific archive-log settings. |
| **Salesforce** | SaaS source, via the Pub/Sub Lite API. No binary log involved. |

Datastream also supports **Kafka** as a source, which is how a Datastream
pipeline can consume events from Confluent — and is the bridge to the
second path in this course.

### The read consistency window

This is the most important tuning knob, and the one that most affects your
latency SLA.

When a transaction commits, its changes are in the log — but a concurrent
transaction might commit immediately afterwards and be *read* first. If
Datastream read the log out of order, it would apply changes in the wrong
sequence.

The **read consistency window** is how long Datastream waits before
reading a transaction's changes, to be sure it sees them in order.

```text
  transaction A commits at t=0
  transaction B commits at t=0.1

  with a 5s window, Datastream reads A's changes at t≈5
  and B's at t≈5.1 — in order. Correct.

  with a 0s window, it might read B first. Out of order.
```

The trade-off:

| Window | Latency floor | Correctness |
|---|---|---|
| `1s` | ~1 second | Usually fine for a single-writer database |
| `5s` | ~5 seconds | **The usual choice.** Safe for normal write loads |
| `10s` | ~10 seconds | Safe under heavy concurrent write load |

The window must exceed the **worst-case gap between two commits that
Datastream might read out of order**. Under normal load that is
milliseconds, so 5 seconds has enormous headroom. Under a heavy write
burst it can be closer.

**Set the SLA floor to the window.** A 5-second window means a 5-second
latency floor, plus the merge time. Anyone who promises "sub-second
replication" with a 5-second window is either wrong or has changed the
window.

### The replication user

Datastream does not use your application user. It needs its own, with
elevated privileges:

```sql
-- MySQL
GRANT SELECT, REPLICATION SLAVE, REPLICATION CLIENT ON *.* TO 'datastream_user'@'%';

-- Postgres (wal_level = logical)
CREATE USER datastream_user WITH REPLICATION PASSWORD '...';
GRANT pg_read_all_data ON ALL TABLES IN SCHEMA public TO datastream_user;
GRANT USAGE ON SCHEMA public TO datastream_user;
```

`REPLICATION SLAVE` is the privilege that lets it read the binary log.
`SELECT` lets it read the tables during a backfill.

### The network path

Datastream does not reach your database over the public internet by
default. It uses a **VPC peering** established through a network config:

```text
  Datastream ──VPC peering──> your VPC ──> your database
       │
       └─ static IP allocated from a reserved range
```

The database's firewall must allow the Datastream **IP allocation's**
address. This is a common first-run failure: the connection profile has
the right hostname, but the source's firewall has not been opened to the
allocated IP.

---

## 🛠️ Hands-On: Preparing a Source

### MySQL configuration

```ini
# /etc/mysql/mysql.conf.d/datastream.cnf
[mysqld]
log_bin                  = /var/log/mysql/mysql-bin.log
binlog_format            = ROW
binlog_row_image         = FULL
binlog_expire_logs_seconds = 604800
server_id                = 1
gtid_mode                = ON
enforce_gtid_consistency = ON
```

Two of these are non-negotiable for CDC:

- `binlog_format=ROW` — CDC cannot use statement format at all.
- `binlog_row_image=FULL` — without it, before images are incomplete.

`gtid_mode=ON` is not required by Datastream, but it is what lets the
replication user reconnect after a failover without re-reading the log
from the beginning.

Verify the settings are live:

```sql
SHOW VARIABLES LIKE 'binlog_format';
SHOW VARIABLES LIKE 'binlog_row_image';
```

```text
+---------------+-------+
| Variable_name | Value |
+---------------+-------+
| binlog_format | ROW   |
+---------------+-------+
| binlog_row_image | FULL |
+---------------+-------+
```

### The replication user

```sql
CREATE USER 'datastream_user'@'%' IDENTIFIED BY 'a-strong-password';
GRANT SELECT, REPLICATION SLAVE, REPLICATION CLIENT ON *.* TO 'datastream_user'@'%';
FLUSH PRIVILEGES;
```

### Postgres configuration

```ini
# postgresql.conf
wal_level = logical
max_replication_slots = 10
max_wal_senders = 10
```

```sql
CREATE USER datastream_user WITH REPLICATION PASSWORD 'a-strong-password';
GRANT pg_read_all_data ON ALL TABLES IN SCHEMA public TO datastream_user;
GRANT USAGE ON SCHEMA public TO datastream_user;
```

Postgres's equivalent of the binary log is the **WAL**, and its equivalent
of the replication privilege is `REPLICATION`. The logical replication
**slot** is what tracks the consumer's position, so the WAL is not
truncated past a disconnected reader.

### The Terraform configuration

The course's `project/terraform/` directory creates the whole setup. The
parts that matter for the source:

```hcl
resource "google_datastream_mysql_source_config" "source" {
  location = var.region
  source_id = var.source_config_id

  source_connection_profile_id = google_datastream_mysql_connection_profile.source.connection_profile_id

  mysql_source_config {
    include_tables {
      table_included = var.included_tables
    }

    exclude_tables {
      table_excluded = var.excluded_tables
    }

    read_from_transaction {
      read_from_transaction {
        read_consistency_window = var.read_consistency_window
      }
    }
  }
}
```

### Model the latency floor

```python
# The latency floor is the consistency window plus the merge time.
CONSISTENCY_WINDOW_SECONDS = 5
MERGE_TIME_SECONDS = 0.3

latency_floor = CONSISTENCY_WINDOW_SECONDS + MERGE_TIME_SECONDS
print(f"latency floor: {latency_floor:.1f}s")

assert latency_floor > 5.0, "the SLA must be at least the consistency window"
```

```text
latency floor: 5.3s
```

---

## 🛠️ Common Errors and Fixes

### `Failed to connect to source host: Connection refused`

The host and port are wrong, or nothing is listening. Check from inside
the VPC:

```bash
gcloud compute ssh your-vm --command="nc -zv 10.0.0.3 3306"
```

### `Connection timed out` (rather than refused)

Almost always a **firewall** problem. The connection profile is right, but
the source's firewall has not been opened to the Datastream IP allocation's
address. Find that address:

```bash
gcloud datastream network-configs ip-pools list \
    --location=us-central1 --network-config=network-config
```

### `User does not have the REPLICATION SLAVE privilege`

The replication user is missing a privilege, or the grants were not
flushed:

```sql
SHOW GRANTS FOR 'datastream_user'@'%';
FLUSH PRIVILEGES;
```

### `binlog_format is not ROW`

Datastream rejects the source. Fix it in the MySQL configuration and
restart the server.

### `Row-based binlog logging is not enabled for the source`

The same problem, reported differently. Check `SHOW VARIABLES`.

### Changes are missing for some tables

They were not in the `include_tables` list. A Datastream source captures
only the tables you name:

```bash
gcloud datastream source-configs describe mysql-source \
    --location=us-central1 --format="value(mysqlSourceConfig.includeTables)"
```

### The stream is running but the table is empty

The stream has no tables to capture, or the destination has the wrong
merge key. Check the stream's state first:

```bash
gcloud datastream streams describe main-stream \
    --location=us-central1 --format="value(streamState)"
```

---

## 💡 Production Notes

- **`binlog_format=ROW` and `binlog_row_image=FULL` are not
  defaults.** MySQL's default for `binlog_format` is `ROW` in modern
  versions, but `binlog_row_image` defaults to `FULL` too — while
  `wal_level` in Postgres defaults to `replica`, which **must** be
  changed to `logical`. Verify on every source.
- **The replication user is a privileged credential.** It can read the
  whole binary log. Store it in Secret Manager, rotate it, and scope it
  to the specific tables where the connector supports it.
- **Set the latency SLA from the consistency window**, not from a
  measurement of a quiet period. A quiet period will show you the best
  case.
- **Watch the log retention.** If the reader disconnects for longer than
  `binlog_expire_logs_seconds`, the log is truncated and the stream must
  do a fresh backfill. Postgres's replication slots prevent this, at the
  cost of holding WAL on disk — which is its own outage risk.
- **Exclude the tables you do not need** at the source, not at the
  destination. Capturing a high-churn audit table wastes log bandwidth and
  merge throughput for data you will filter out anyway.

---

## 🔑 Key Takeaways

- CDC reads the **write-ahead log**, which is sequential, replayable, and
  sees deletes and transaction boundaries.
- `binlog_format=ROW` is mandatory. `binlog_row_image=FULL` is strongly
  recommended — `MINIMAL` breaks before images.
- Postgres needs `wal_level=logical` and a **replication slot**.
- The **read consistency window** sets your latency floor. 5 seconds is the
  usual choice.
- The replication user needs `REPLICATION SLAVE` and `SELECT`, and its
  password belongs in Secret Manager.
- A **timeout** is a firewall problem; a **refused** connection is a wrong
  host or port.

---

## 📚 Practice Exercises

1. **Calculate your latency floor.** Given a 10-second consistency window
   and a measured merge time of 0.4 seconds per batch, write the SLA
   statement you would give a stakeholder.

2. **Model the out-of-order risk.** Two transactions commit 50 ms apart.
   Explain what happens with a 0-second window, a 1-second window and a
   5-second window.

3. **Write the privilege grants.** For a MySQL source capturing only
   `inventory.customers` and `inventory.orders`, write the narrowest
   grants that still work, and explain why `ON *.*` is what the
   documentation recommends anyway.

4. **Diagnose the timeout.** Write the sequence of `gcloud` and `gcloud
   compute ssh` commands you would run, in order, to find out whether a
   source connection failure is a firewall, a routing, or a listening
   problem.

5. **Reflection.** Your source table's `updated_at` column is indexed and
   you poll every 5 minutes. Calculate how many rows you read per day, and
   compare it to the number of rows that actually change. What does the
   ratio tell you about whether CDC is worth it here?

---

## 📖 Further Reading

- MySQL binary log configuration — https://dev.mysql.com/doc/refman/8.4/en/replication-options-binary-log.html
- Postgres logical replication — https://www.postgresql.org/docs/current/logical-replication.html
- Datastream's source configuration — https://cloud.google.com/datastream/docs/sources-overview
- Debezium's MySQL connector — https://debezium.io/documentation/reference/connectors/mysql.html
