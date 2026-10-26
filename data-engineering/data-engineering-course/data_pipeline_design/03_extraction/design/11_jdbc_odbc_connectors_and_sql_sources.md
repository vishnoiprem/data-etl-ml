# 11 — JDBC/ODBC Connectors and SQL Sources

> **Lesson 11 of 30 — Extraction**

Most pipelines extract from SQL databases. The JDBC connector is
the workhorse: it opens a connection, runs a query, returns rows.
The senior move is to know how to do this *reliably* — watermarks,
slot management, and the failure modes that catch you at 3 AM.

---

## 1. What JDBC is

JDBC (Java Database Connectivity) is the standard API for talking
to relational databases from Java. Every major database has a
JDBC driver: Postgres, MySQL, Oracle, SQL Server, Snowflake, Redshift.

ODBC is the cross-platform equivalent. Most data tools (Airflow,
dbt, Spark) use JDBC under the hood. The 2026 default for new
pipelines is JDBC unless you need ODBC for a legacy Windows
system.

In Python, the equivalent is `psycopg`, `mysql-connector`, or
`pyodbc`. They all speak the same protocol: open connection,
execute query, fetch rows.

---

## 2. The connection pattern

```python
import psycopg

conn = psycopg.connect(
    host="prod-db.example.com",
    port=5432,
    dbname="orders",
    user="pipeline",
    password=os.environ["DB_PASSWORD"],
    connect_timeout=10,
)
```

The senior move: never hardcode credentials. Use a secret manager
(Vault, AWS Secrets Manager, GCP Secret Manager). Rotate the
credentials every 90 days. Use a dedicated user with read-only
permissions on the tables you need.

---

## 3. The watermark pattern

The most common JDBC extraction pattern is the *watermark* — track
the last `updated_at` value, query only rows after it.

```python
def extract_users(conn, last_watermark):
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, name, email, country, updated_at
        FROM users
        WHERE updated_at > %s
        ORDER BY updated_at
        LIMIT 10000
        """,
        (last_watermark,),
    )
    rows = cur.fetchall()
    if not rows:
        return [], last_watermark
    new_watermark = max(row["updated_at"] for row in rows)
    return rows, new_watermark
```

The pitfalls:

| Pitfall | Mitigation |
|---|---|
| `updated_at` in local timezone | Always compare in UTC. |
| Multiple rows at same `updated_at` | Track `(watermark, last_pk)` as a tuple. |
| Clock skew between source and pipeline | Reject rows with `updated_at > NOW() + 5 min`. |
| Source is read-only / no `updated_at` | Fall back to full load, or CDC. |

---

## 4. The keyset pattern

An alternative to the watermark is the *keyset* — track the
highest-seen primary key:

```python
def extract_users_keyset(conn, last_id):
    cur = conn.cursor()
    cur.execute(
        "SELECT id, name, email FROM users WHERE id > %s ORDER BY id LIMIT 10000",
        (last_id,),
    )
    return cur.fetchall()
```

This works when the primary key is monotonic and the data is
append-only. The benefit: no clock-skew issues. The cost: doesn't
catch updates to existing rows.

---

## 5. Postgres replication slots

Postgres has a built-in mechanism for *exactly-once* extraction:
the replication slot. A slot is a server-side cursor that
remembers the consumer's position in the WAL.

```sql
-- The replication slot pattern
SELECT pg_create_logical_replication_slot('pipeline_slot', 'pgoutput');
```

Debezium uses replication slots. The slot is bound to a consumer;
if the consumer disconnects, the slot *holds* the WAL until the
consumer reconnects. The pitfall: if the consumer is gone forever,
the slot fills up disk. Postgres will eventually stop accepting
writes when the disk is full.

The senior move: monitor slot lag.

```sql
-- The slot lag query
SELECT slot_name,
       pg_size_pretty(pg_wal_lsn_diff(pg_current_wal_lsn(), restart_lsn)) AS lag_bytes
FROM pg_replication_slots;
```

If `lag_bytes` is growing, the consumer is falling behind. Page
on-call. The senior move is to name this query unprompted.

---

## 6. Connection pooling

A pipeline that opens a new connection per run is slow and
fragile. The senior pattern is a *connection pool*:

```python
from psycopg_pool import ConnectionPool

pool = ConnectionPool(
    conninfo="host=... dbname=... user=... password=...",
    min_size=2,
    max_size=10,
    timeout=30,
)

with pool.connection() as conn:
    cur = conn.execute("SELECT ...")
    rows = cur.fetchall()
```

The pool keeps `min_size` connections open and grows to `max_size`
under load. The `timeout` is the max time to wait for a free
connection. The senior move: name the timeout. "If the pool
exhausts, the pipeline blocks. I'd alert on pool wait time > 5
seconds."

---

## 7. The query patterns

The three SQL extraction patterns in production:

**Pattern 1: incremental by `updated_at`** (covered above)

**Pattern 2: keyset by primary key** (covered above)

**Pattern 3: partitioned by date**

```sql
SELECT *
FROM events
WHERE event_date = '2024-01-15'
  AND id > :last_id
ORDER BY id
LIMIT 10000;
```

This is the right pattern for time-series data: events, logs,
clickstream. The pipeline processes one partition at a time,
commits, then moves to the next. The benefit: clear progress
reporting, easy backfill (just re-run a partition).

---

## 8. The failure modes

| Failure | Mitigation |
|---|---|
| Source DB down | Retry with backoff; alert after 5 min. |
| Connection pool exhausted | Increase pool size; alert on wait time. |
| Replication slot lag growing | Page on-call; check consumer. |
| Schema change breaks query | Schema contract test (Lesson 12). |
| Long-running query holds lock | Use `SET LOCAL statement_timeout = 60000` (60s). |
| Auth expired | Use Vault; rotate every 90 days. |

The senior move: name the long-running-query failure mode. "A
query without a `LIMIT` or `statement_timeout` can hold a lock for
hours, blocking the source DB. Every production query needs both."

---

## 9. The interview answer

> "For the SQL sources I'd use the JDBC connector with a connection
> pool. The extraction pattern is incremental by `updated_at` with
> a `(watermark, last_pk)` tuple for tie-breaking. The watermark is
> stored in the destination's pipeline_state table. For Postgres
> specifically I'd use a replication slot for exactly-once
> guarantees; for MySQL I'd use the binlog directly. The
> reliability story: the pool is sized to the peak load, the
> `statement_timeout` is 60s, and the slot lag is monitored
> continuously."

That single paragraph covers: connection management, watermark
pattern, Postgres-specific feature, and three reliability
mechanisms. Senior answer in 30 seconds.

---

## Try it

Look at the most recent SQL extraction you've worked on. What was
the pattern (watermark, keyset, full)? Where was the watermark
stored? What happened on restart? Was there a `statement_timeout`?
If not, the pipeline is one bad query away from a source DB
outage.
