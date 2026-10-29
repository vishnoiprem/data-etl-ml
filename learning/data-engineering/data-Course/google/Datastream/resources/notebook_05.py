#!/usr/bin/env python3
"""
notebook_05.py — build notebook 05, Kafka → Cloud Run → Cloud SQL.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from build_notebooks import code, md, notebook  # noqa: E402


def build() -> dict:
    """Build notebook 05.

    Returns:
        The notebook dict.
    """
    return notebook([
        md("""
# 05 · Kafka → Cloud Run → Cloud SQL

> **Module 4 · The Confluent Kafka Path · Lecture 4.1**

In this notebook you will:

- Build the second pipeline shape in this course: a **Kafka topic → Cloud Run
  Function → Cloud SQL PostgreSQL** path
- Implement the function's three stages — **fetch the secret**, **parse the
  message**, **write the row** — and test each one
- Prove that the SQL is **parameterised**, not string-built, by attacking it
- Understand the delivery-semantics difference between Kafka and a CDC log,
  and what it means for your table

This is the path Confluent's own **Google Cloud Functions sink connector**
drives, and it is the second half of the hands-on course.
"""),
        code("""
import json
import sys
from pathlib import Path

COURSE_ROOT = Path.cwd()
if not (COURSE_ROOT / "project").exists():
    COURSE_ROOT = Path.cwd().parent
if not (COURSE_ROOT / "project").exists():
    COURSE_ROOT = Path.cwd().parent.parent

sys.path.insert(0, str(COURSE_ROOT / "project"))

from kafka_to_gcp import build_insert_sql, parse_transaction, replay_messages

print(build_insert_sql())
"""),
        md("""
## 1. Why a second pipeline shape?

Datastream is for **databases**. Kafka is for **everything else** — event
streams, application logs, third-party feeds, and, increasingly, the output
of a CDC pipeline that somebody wants to fan out to many consumers.

The two shapes have different characters:

| | Datastream → BigQuery | Kafka → Cloud Run → Cloud SQL |
|---|---|---|
| Source | A database's binary log | A Kafka topic |
| Semantics | **Stateful** — the table converges | **Stateless** — each message is a fact |
| Delivery | Exactly-once within the merge | **At-least-once** |
| Storage | BigQuery (columnar) | PostgreSQL (row-based) |
| Typical latency | Seconds | Milliseconds |
| State kept | The full current table | None, unless you dedupe |

The last row is the one that catches people. **A Kafka consumer has no
memory.** It receives a message, does something, and forgets it. If the
same message arrives twice, it is processed twice. That is the difference
between the two paths, and it is why the Datastream table converges and the
Cloud SQL table can double-count.

## 2. Stage one — the secret

The database password must never be in the function's source, its
environment variables, or its container image. Secret Manager is where it
goes, and the function reads it at runtime.
"""),
        code("""
import os

# The local path: an environment variable standing in for Secret Manager.
os.environ.setdefault("SECRET_VALUE", "local-dev-password")

from kafka_to_gcp import fetch_secret

print("fetched secret:", fetch_secret("db-password"))
"""),
        md("""
Notice the **cache**. The function fetches the secret once per instance
and keeps it in module scope, because Cloud Run reuses the instance across
invocations. Fetching on every call would add a round trip to every message.

The trade-off: a rotated secret is not picked up until the instance is
restarted. That is acceptable for a database password and unacceptable for
a short-lived token, which is why the two should be cached differently.

## 3. Stage two — parse

The parser validates rather than coerces. It rejects a message that is
missing a field, rather than inserting a NULL.
"""),
        code("""
valid = {
    "transaction_id": "t00000001",
    "customer_id": "c000001",
    "amount": 42.50,
    "currency": "EUR",
    "product_id": "p0001",
    "channel": "web",
    "timestamp": "2026-01-15T10:30:00Z",
}

row = parse_transaction(json.dumps(valid))
print(json.dumps(row, indent=2))
"""),
        code("""
# Every rejection path, one by one.
missing_amount = {k: v for k, v in valid.items() if k != "amount"}

bad_cases = [
    ("not json",            "{not json"),
    ("not an object",       "[1,2,3]"),
    ("missing amount",      json.dumps(missing_amount)),
    ("non-numeric amount",  json.dumps({**valid, "amount": "lots"})),
    ("negative amount",     json.dumps({**valid, "amount": -5})),
    ("unknown currency",    json.dumps({**valid, "currency": "XYZ"})),
    ("unknown channel",     json.dumps({**valid, "channel": "pigeon"})),
]

for label, payload in bad_cases:
    try:
        parse_transaction(payload)
        print(f"{label:<22} -> ACCEPTED (unexpected!)")
    except ValueError as exc:
        print(f"{label:<22} -> rejected: {exc}")
"""),
        md("""
## 4. Stage three — write

Here is the security property that matters most in this whole path.

**The INSERT must be parameterised.** The value is passed to the driver as
data, not formatted into the SQL string. That is not a style preference —
it is the difference between storing a string that happens to contain a
quote and executing that string.
"""),
        code("""
class RecordingCursor:
    def __init__(self, sink):
        self.sink = sink

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def execute(self, statement, values=None):
        self.sink.append((statement, values))


class RecordingConnection:
    def __init__(self):
        self.statements = []
        self.commits = 0

    def cursor(self):
        return RecordingCursor(self.statements)

    def commit(self):
        self.commits += 1


# A message whose product_id tries to break out of the string.
attack = {**valid, "product_id": "p0001'; DROP TABLE transactions; --"}
row = parse_transaction(json.dumps(attack))

connection = RecordingConnection()
from kafka_to_gcp import ingest_transaction
ingest_transaction(row, connection=connection)

statement, values = connection.statements[0]
print("The statement the driver received:")
print("   ", statement)
print()
print("The values the driver received:")
for value in values:
    print("   ", repr(value))
print()
print("Does the statement contain 'DROP TABLE'? ", "DROP TABLE" in statement)
print("Is the payload in the VALUES?           ", any("DROP TABLE" in str(v) for v in values))
"""),
        md("""
The `DROP TABLE` text is in the **values**, not in the statement. The
driver sends it as a string literal, and PostgreSQL stores it as data. The
table is safe.

If the code had built the statement with an f-string, the statement would
have contained the `DROP TABLE` and the table would be gone. Here is that
version, for contrast — and note that it is *exactly* the kind of code that
passes every test, because the test data has no quotes in it.
"""),
        code("""
# The vulnerable version — for contrast only. Never write this.
def vulnerable_insert(connection, row):
    values = ", ".join(f"'{row[c]}'" for c in
                       ("transaction_id", "customer_id", "amount", "currency",
                        "product_id", "channel", "timestamp", "ingested_at"))
    statement = f"INSERT INTO transactions VALUES ({values})"
    connection.statements.append((statement, None))
    return statement

vulnerable = RecordingConnection()
bad_statement = vulnerable_insert(vulnerable, row)
print(bad_statement)
print()
print("Contains 'DROP TABLE'? ", "DROP TABLE" in bad_statement)
"""),
        md("""
## 5. Running the whole path

The `kafka_to_gcp.py` script replays a recorded message log, so the full
path is testable with no broker and no database.
"""),
        code("""
messages = [
    line.strip()
    for line in (COURSE_ROOT / "sample_data" / "transactions.ndjson").read_text().splitlines()
    if line.strip()
]
print("messages to replay:", len(messages))

summary = replay_messages(messages)
print()
print(f"ingested : {summary['ingested']}")
print(f"rejected : {summary['rejected']}")
"""),
        md("""
## 6. The delivery-semantics problem

Now the important part. Kafka is **at-least-once**, and a Cloud Function
invocation can fail *after* writing to the database but *before* the
connector marks the message as consumed. The message is then redelivered,
and the row is written twice.

Let us demonstrate it.
"""),
        code("""
# A message delivered twice, because the first attempt's acknowledgement
# was lost.
delivery = [json.dumps(valid), json.dumps(valid)]

connection = RecordingConnection()
summary = replay_messages(delivery, connection=connection)

print(f"messages delivered : {summary['messages']}")
print(f"rows written       : {len(connection.statements)}")
print(f"commits            : {connection.commits}")
print()
print("The same transaction_id was written twice.")
"""),
        md("""
Two rows, one transaction. The table now double-counts.

### The fixes, in order of preference

**1. A unique constraint on the business key.** The cheapest, most robust
fix, and the one you want at the database level regardless:

```sql
CREATE TABLE transactions (
    transaction_id TEXT PRIMARY KEY,
    ...
);
```

With the constraint, the second insert raises a duplicate-key error, which
you catch and treat as success. The table cannot double-count, even if the
application gets it wrong.

**2. An idempotency key in the payload.** The producer includes a stable
id, and you `INSERT ... ON CONFLICT DO NOTHING`.

**3. Deduplicate in the function**, with a lookup table of processed ids.
Works, but it adds a read and a write per message, and it has its own
failure modes.

### The general rule

> The **database** is the last line of defence. Enforce uniqueness where
> the data lives, not only in the application that writes it. The
> application will be retried; the constraint will not.

## 7. A note on Cloud Run versus Cloud Functions

The course uses Cloud Functions because Confluent's sink connector targets
it directly. Cloud Run services are the newer, more flexible option and
are what you would build today for a new pipeline.

| | Cloud Functions (gen2) | Cloud Run |
|---|---|---|
| Trigger | Event-driven | Any — HTTP, background, scheduled |
| Concurrency | 1 per instance by default | Configurable, up to 1000 per instance |
| Cold start | Yes | Yes, but min-instances can remove it |
| Best for | Small, event-driven handlers | Longer requests, higher throughput |

The difference that bites in production: **Cloud Run lets you set
`min-instances`**, so a cold start never happens. For a stream consumer
with a latency SLA, that matters a great deal.

## What to take away

- Kafka → Cloud Run → Cloud SQL is a **stateless** path. The database must
  enforce idempotency, not the application.
- Parameterise every INSERT. The test with a quote in the payload is the
  test that matters.
- A `PRIMARY KEY` on the business key is the cheapest correct fix for
  at-least-once delivery.
"""),
    ])


if __name__ == "__main__":
    from build_notebooks import NOTEBOOKS

    out = Path(sys.argv[1]) if len(sys.argv) > 1 else NOTEBOOKS / "05-kafka-to-gcp-pipeline.ipynb"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(build(), indent=1) + "\n", encoding="utf-8")
    print(f"wrote {out}")
