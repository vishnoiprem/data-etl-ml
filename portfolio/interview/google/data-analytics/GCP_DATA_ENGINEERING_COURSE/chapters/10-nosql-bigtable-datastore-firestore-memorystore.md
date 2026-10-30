# 2.5 — NoSQL: Bigtable, Datastore, Firestore, Memorystore

> **Section 2 · Storage & Databases · Lecture 2.5 · 8:00**

## 🎯 What you will learn

- The four NoSQL data models — key-value, document, wide-column, graph — and what each optimises for
- Why relational modelling fails at scale, and the specific problem each NoSQL model solves
- **Cloud Bigtable**: the storage model, row keys as the primary design decision, column families, and the architecture
- Row-key design in depth: salting, prefix/suffix, key rotation, and hot spotting
- **Cloud Datastore**: entity kinds, key vs non-key entities, property indexes, and the eventual-consistency trap
- **Firestore**: documents, subcollections, indexes, offline sync, and the SDK model
- **Memorystore**: Redis and Memcached, and the decision between them
- The Redis vs Memcached comparison, from the data structure level up
- Where each service fits, and where none of them is the right answer

---

## 🧠 Concept

### The four data models

"NoSQL" is not a specification; it is a family of trade-offs. There are four data models worth understanding, and each one buys a specific property by giving up a different one.

```text
KEY-VALUE      "give me a value for a key"                — Redis, Memorystore
WIDE-COLUMN    "give me a row, and I will ask for columns" — Bigtable, HBase
DOCUMENT       "give me a tree-shaped object"              — Firestore, Datastore, MongoDB
GRAPH          "give me the neighbours of a node"          — Neo4j, Spanner Graph
```

The relational model optimises for **arbitrary ad-hoc queries over normalised data**. Every NoSQL model gives that up in exchange for something:

| Model | Gains | Gives up |
|---|---|---|
| Key-value | Extreme speed and scale; trivial horizontal partitioning | Any query that is not a key lookup |
| Wide-column | Columnar storage, sparse columns, per-column-family configuration, enormous scale | Joins, secondary indexes, ad-hoc predicates |
| Document | Natural nesting, flexible schema, whole-object read/write | Cross-document queries are expensive; no joins |
| Graph | Constant-hop traversal regardless of depth | Everything else; very specialised |

For a data engineer, the important thing to understand is **the access pattern drives the model**. You do not choose "document database" because your team likes JSON. You choose it because the application's dominant operation is "fetch this whole aggregate by id" — a document fetch is one round trip, whereas the equivalent relational query is a join across four tables.

### Bigtable: the storage model

Cloud Bigtable is Google's take on Google's Bigtable, the paper that inspired HBase, Cassandra, and most of the NoSQL world. It is a **wide-column store** and it is the most technically demanding of the four services in this chapter.

**The physical model.** Bigtable is a sparse, sorted, multi-dimensional map:

```text
Table
 └─ Row (identified by a row key: bytes)
     └─ Column family (a namespace of columns, configured at table creation)
         └─ Column (identified by a qualifier: bytes)
             └─ Cell
                 ├─ value: bytes
                 ├─ version: timestamp (microsecond precision, server-assigned)
                 └─ timestamp: when the cell was written
```

Four things follow from this structure, and each one is a design decision you must make:

1. **Rows are sorted by row key.** A range scan over row keys is a contiguous read of a contiguous slice of the tablet. This is the single most important property of Bigtable, and the entire row-key design strategy follows from it.
2. **Columns are sparse.** A row does not need to have every column in a family. Absent is free. This is how Bigtable stores a wide, sparse, evolving schema without paying for the nulls.
3. **Column families are the unit of physical configuration.** Each family has its own storage type (SSD or HDD), its own garbage-collection policy, and its own replication. A family can be dropped or altered without rewriting the table's data. **The convention is one family per access pattern**: `cf1` for the hot columns you always read, `cf2` for the cold ones you rarely read. This lets Bigtable keep the hot family on SSD and the cold family on HDD in the same row.
4. **Cells are versioned.** Writes create new versions with a server-assigned timestamp. Bigtable keeps only the configured number of versions per cell, garbage-collecting the rest. Reads can ask for a specific timestamp and get a point-in-time view.

**The architecture.**

```text
Client library (HBase / Go / Java / Python)
     │
     ▼
  Tablet ────────── a sorted range of rows, served by one tablet server
     │
     ▼
  SSTable ───────── immutable, sorted, on-disk data files (LSM tree)
     │
     ▼
  Memtable ─────── the in-memory write buffer
```

An LSM tree: writes go to an in-memory memtable and are flushed to disk as an immutable sorted table (SSTable) when it fills. Reads consult the memtable and then the SSTables, with a compaction process merging them and dropping obsolete versions. The trade is **fast writes, slightly more expensive reads**. Bigtable added a write-ahead log, and memtable/SSTable flushes are the reason a Bigtable table can absorb enormous write rates.

**The tablet** is the unit of replication and splitting, exactly as in Spanner. It is replicated across zones; the tablet server is the leader.

### Row-key design: the whole game in Bigtable

Because rows are sorted by key and a range scan is a contiguous read, **the row key is your schema**. A badly designed row key produces a table that cannot be read efficiently, cannot be split evenly, or has a permanent hotspot. A well-designed one makes the common queries fast and the table self-balancing.

**Problem 1 — the hotspot.** Bigtable splits tablets at the **median** of the key range. If your keys all begin with the same prefix and increase monotonically (a timestamp, a sequence number), every new row lands at the end of the key range — the same tablet. That tablet's server becomes a write bottleneck, and the table's write throughput is capped at one server's capacity no matter how many nodes you add.

The fix is **salting**: insert a hash component so that keys with the same logical prefix scatter across the key space.

```text
BAD:  20260115T000000#e00000001
      20260115T000001#e00000002     → all in one tablet's tail

GOOD: 3f#20260115T000000#e00000001
      a7#20260115T000001#e00000002   → spread across the key space
```

The cost of salting: **you can no longer do a contiguous range scan over the logical prefix**, because the salt is the first component. A range scan over `20260115*` now touches every tablet. This is the fundamental trade: **hot-spot avoidance vs range-scan locality**. There is no free lunch, and you must decide which your workload needs.

**Problem 2 — the read pattern.** You want a query like "all events for user U in time range T". If the row key is `(user_id, timestamp, event_id)`, that is a contiguous range scan and it is fast and cheap. If the row key is `(event_id)`, the query is a scatter-gather across the whole table — every row is a separate lookup, and the cost is proportional to the result size times the number of tablets touched.

**Problem 3 — key rotation.** Row keys accumulate. If you use a timestamp-first key and never delete old rows, the table grows forever and your range scans get slower as the key space grows. Two mitigations:

- **Key rotation**: periodically start a new key family so the old data occupies a contiguous prefix you can drop wholesale. For example, keys of the form `2026-01#user#timestamp#event` can be deleted by dropping the `2026-01#` range.
- **Column-family TTL**: Bigtable's garbage collection policy can expire cells based on the timestamp in their *column qualifier* (the "cell TTL" mechanism). This is how you get time-to-live on a per-cell basis.

**The composite-key patterns worth memorising:**

| Key shape | Use when |
|---|---|
| `hash(salt)#entity_id#timestamp#seq` | Even write distribution; you accept losing range-scan locality |
| `entity_id#reverse_timestamp#seq` | Range scans by entity, newest first; reads dominate |
| `timestamp#entity_id` | Time-ordered scans across all entities; risky for writes |
| `entity_id#timestamp` | The default for most event/time-series workloads |

Note the second pattern: `reverse_timestamp` — a timestamp *inverted* so that descending order is ascending in the sort. Bigtable sorts keys lexicographically, so to read "newest first" you either scan backwards or store the timestamp inverted. In practice, storing the timestamp inverted is more reliable than relying on the client's scan direction, because a backwards scan still reads the same number of tablets.

**The Bigtable-specific trap: the column qualifier.** Bigtable lets you put arbitrary bytes in the column qualifier. Teams use it as a mini secondary index: `user#u000914#20260115`. This works, and it is a well-known Bigtable technique, but the consequences must be understood:

- The qualifier becomes part of the key, so it changes the sort order of the columns within the family.
- You cannot *scan* for a qualifier prefix efficiently the way you would scan a row-key prefix — the qualifier ordering is within a row, and a qualifier-only query means scanning every row in the table.
- The index must be written in the same transaction as the primary cell, or it goes stale.

Use it for a **point lookup** (one row, one qualifier), not for a **range query** across many rows.

### Datastore: entity kinds and the key/non-key distinction

Cloud Datastore is a document database with a **non-relational, schema-optional** model, descended from Google's original App Engine Datastore.

**Entities and kinds.** A *kind* is a table. An *entity* is a row. An entity has a **key** (an identifier, optionally with a parent) and a set of **named properties**. Properties can be scalars, lists, or nested entity values.

**The key vs non-key distinction is the thing to get right.** A **key entity** has a user-assigned key — you choose the identifier. A **non-key entity** has a server-assigned, monotonically increasing numeric ID.

The distinction is not cosmetic; it changes how the datastore indexes and how you write queries:

- **Key entities** are looked up by `key_name` or `key_id`. A key entity's key is **not** indexed as a property in the same way, and a key entity **cannot be used in an ancestor/descendant query** by key path without a property.
- **Non-key entities** get an ID from the datastore, which is allocated from a per-kind counter. This gives you **globally increasing IDs** — which is genuinely useful for chronological ordering without an index — but it means **the ID is assigned by the datastore and you cannot choose it**, and IDs for a kind are allocated in blocks, so they are not perfectly gapless.
- **Ancestor paths.** Every entity can have a **parent**, forming a tree. A query with an ancestor filter returns the entity and all its descendants. This is the closest thing Datastore has to a relational join, and it is a *range scan* over the tree — efficient, but only if the tree is not too deep.

**Indexes.** Datastore maintains **single-property indexes** automatically on every property, plus **composite indexes** you declare explicitly. The critical, counter-intuitive rule:

> **A composite index is not created automatically. If you query on two or more properties together with an equality filter and an inequality filter, the query fails unless a matching composite index exists.**

The failure mode is distinctive and worth memorising:

```text
google.api_core.exceptions.BadRequest: 400 The query requires a composite index.
```

The index definition must exactly mirror the query's shape: the equality-filtered properties first (in a consistent order), then the inequality-filtered property, then the sort orders. The `gcloud datastore indexes composite create` command takes the definition explicitly.

**Consistency.** This is where Datastore catches people out:

- **Ancestor queries are strongly consistent.** Within a single entity group (a parent and its descendants), reads see the latest committed writes.
- **Non-ancestor queries are eventually consistent** by default. A write is not immediately visible to a global query. You can request strong consistency on a non-ancestor query (a `read_consistency` option), at the cost of increased latency and a higher chance of being unavailable.

The consequence: **if your application's correctness depends on reading its own just-written data, use an ancestor query or an explicit strong read.** A dashboard that reads what a job just wrote, with an eventually consistent non-ancestor query, will intermittently show stale data. This is a genuinely surprising behaviour for a "database" and it comes directly from the architecture — Datastore's datastore group is replicated and the replicas converge asynchronously.

### Firestore: documents, subcollections, and sync

Firestore is the successor to Datastore, with a mobile-first, offline-capable model and a cleaner API.

**Documents and collections.**

```text
Firestore
 └─ Collection: "users"
     └─ Document: users/ana
         └─ Collection: "orders"      (a subcollection)
             └─ Document: orders/o1
```

- A **document** is a set of key-value fields, with an optional nested-map structure. Document IDs are unique within their collection.
- A **collection** is a container of documents.
- A **subcollection** is a collection nested under a document. It has the same structure and API as a top-level collection.

**The critical Firestore modelling rule:**

> **Documents are cheap to read as a unit and expensive to read piecemeal. Data accessed together belongs in the same document; data accessed independently belongs in its own collection.**

Reading a document is one operation regardless of how many fields it has. So a `users/ana` document containing her name, address, and preferences is one read. Splitting the address into `users/ana/addresses/home` means a second read. Firestore bills per document read, so this is a cost rule as well as a latency rule.

The counter-rule: **a document has a hard size limit of about 1 MiB.** So you cannot put an unbounded list of orders inside a user document. This is where subcollections earn their keep — a user with 10,000 orders needs a subcollection, not a giant array.

**Subcollection semantics that surprise people:**

- A subcollection's documents do **not** appear in the parent document's `collectionGroup` query unless you query the collection group.
- **Deleting a parent document does not delete its subcollections.** Firestore does not cascade-delete subcollections. This is a well-known data-leak footgun: `delete(doc(users, "ana"))` leaves `users/ana/orders/*` in the database, still billable, still accessible to anyone with permission on that path.
- A `collectionGroup` query spans all collections with the same name, which is how you query across all subcollections in one request.

**Indexes.** Firestore has:
- **Automatic single-field indexes** on every field, and on every nested field.
- **Composite indexes**, which you must declare for any query with more than one equality filter plus an inequality or a sort, and for queries with an `in` clause. The same "requires a composite index" failure appears.
- **Collection group indexes**, which need a `__name__` component.

**Offline persistence and sync.** Firestore's client SDKs maintain a **local cache** on the device and synchronise with the server:

- Writes are applied **optimistically** to the local cache and then sent to the server. The UI updates immediately.
- The SDK listens for changes to the documents it is observing and re-reads them when they change.
- When the device is offline, writes are queued locally and sent when connectivity returns.
- The **conflict resolution** rule is last-write-wins **per document**. Two devices editing the same document offline converge to the last write; there is no merge and no CRDT.

The design implication for a data engineer: **a Firestore document is the unit of conflict resolution and the unit of billing.** If two devices write to the same document, one write wins and the other is silently lost. For a counter or a shared list that two clients edit, you must use `FieldValue.increment()` (an atomic server-side operation) or a transaction, not a read-modify-write from the client.

### Memorystore: Redis and Memcached

Memorystore gives you a **managed in-memory cache** — either Redis or Memcached — running on dedicated nodes in your VPC.

**Redis** is a data structure server. It supports:

- **Strings** — the simplest thing, and the basis for the others.
- **Hashes** — field/value maps, ideal for "object with a few attributes".
- **Lists**, **Sets**, **Sorted Sets** (with scores) — queues, membership, leaderboards.
- **Bitmaps**, **HyperLogLog**, **Streams** (an append-only log with consumer groups — Redis's answer to Kafka-lite).
- **Pub/Sub** — fire-and-forget messaging.

And crucially, Redis supports **persistence**: `RDB` snapshots and `AOF` (append-only file) logs, with configurable durability. A Redis instance can therefore be a system of record for small, hot data — a session store, a rate limiter, a feature-flag store.

**Memcached** is a **pure in-memory key-value cache**. That is the entire feature set: `get`, `set`, `delete`, `add`, `increment`. No data structures beyond a flat string-to-string map, no persistence, no replication, no scripting.

### Redis vs Memcached: the decision

| Dimension | Redis | Memcached |
|---|---|---|
| Data structures | 15+ types | Flat string map only |
| Persistence | RDB snapshots + AOF | **None** — everything is lost on restart |
| Replication | Built-in, with `Sentinel` for failover | None (you run multiple independent instances) |
| High availability | Sentinel / cluster mode | Client-side sharding only, no failover |
| Memory overhead | Higher per key (internal metadata) | Lower — better memory efficiency for simple cached values |
| Max item size | 512 MB | 1 MB (the traditional limit) |
| Transactions | `MULTI`/`EXEC`, Lua scripts | None |
| Pub/Sub, Streams | Yes | No |
| Clustering | Native (hash slots) | Client-side sharding only |
| Memorystore tier | Standard, Standard with HA | Standard, Standard with HA |

**The decision rule:**

- **Choose Memcached** when your use case is *exactly* "cache serialized objects, keyed by id, with a TTL". That is the overwhelming majority of caching use cases, and Memcached does it with less memory overhead and marginally lower latency.
- **Choose Redis** when you need anything beyond that: data structures, persistence, replication with automatic failover, atomic counters, distributed locks, rate limiters with sliding windows, or streams.

The honest default for a new GCP project: **Redis.** The extra capability costs almost nothing extra (Memorystore prices Redis and Memcached instances at similar rates for the same size), and the migration from Redis to Memcached is not possible, whereas the migration from Memcached to Redis is trivial (you just stop using the operations Memcached lacks). Choosing Memcached is a one-way door; choosing Redis is not.

The other point worth making: **if you need multi-region, Memorystore is not the answer.** A Memorystore instance lives in one region. A global cache needs either a per-region instance with a routing layer, or a different service.

---

## 🛠️ Hands-On

### 1. Create a Bigtable instance, cluster, and table

```text
gcloud bigtable instances create events-bt \
    --project=YOUR_PROJECT_ID \
    --display-name="Events Bigtable" \
    --cluster=events-cluster \
    --cluster-zone=us-central1-b \
    --instance-type=PRODUCTION \
    --description="Event store for the course pipeline"

gcloud bigtable instances clusters list instances=events-bt

gcloud bigtable tables create events-bt.events \
    --project=YOUR_PROJECT_ID \
    --column-families=cf-hot,cf-cold \
    --granularity=MILLISECONDS
```

Note the **column families at creation**. You cannot create a family after the table exists — only delete one. And the naming convention `cf-hot`/`cf-cold` is the standard Bigtable practice: one family per access pattern.

Set the family's storage type so the hot family is on SSD:

```text
gcloud bigtable tables update events-bt.events \
    --column-families=cf-hot:SSD,cf-cold:HDD
```

### 2. Write rows with a deliberately designed key

```python
import hashlib
import time
from datetime import datetime, timezone

from google.cloud import bigtable
from google.cloud.bigtable import row_filters


def make_row_key(user_id: str, event_ts: str, event_id: str) -> bytes:
    """Build a salted composite row key.

    The salt is the first component so that writes for the same user do
    not all land on one tablet. The user id and the event timestamp
    follow, so that a scan over one user's time range is a contiguous
    range read of the rows that share the salt — remember that this
    sacrifices locality across the whole user's history.

    Args:
        user_id: The user the event belongs to.
        event_ts: The event timestamp, as an ISO-8601 string.
        event_id: The unique event id.

    Returns:
        The row key, as bytes.
    """
    salt = hashlib.sha1(user_id.encode("utf-8")).hexdigest()[:2]
    return f"{salt}#{user_id}#{event_ts}#{event_id}".encode("utf-8")


def write_events(
    instance_id: str,
    table_id: str,
    events: list[dict],
) -> int:
    """Write events into Bigtable using a column family per access pattern.

    Args:
        instance_id: The Bigtable instance id.
        table_id: The table id.
        events: The events to write. Each needs user_id, event_id,
            event_ts, event_type, region and amount.

    Returns:
        The number of rows written.
    """
    client = bigtable.Client(project="YOUR_PROJECT_ID", admin=True)
    instance = client.instance(instance_id)
    table = instance.table(table_id)

    hot_family = table.column_family("cf-hot")
    cold_family = table.column_family("cf-cold")

    rows = []
    for event in events:
        key = make_row_key(event["user_id"], event["event_ts"], event["event_id"])
        row = table.direct_row(key)
        # Hot family: the columns every read needs.
        row.set_cell("cf-hot", "event_type", event["event_type"], timestamp_micros())
        row.set_cell("cf-hot", "region", event["region"], timestamp_micros())
        # Cold family: the columns only the detail view needs.
        row.set_cell("cf-cold", "amount", str(event["amount"]), timestamp_micros())
        row.set_cell("cf-cold", "user_id", event["user_id"], timestamp_micros())
        rows.append(row)

    table.mutate_rows(rows)
    return len(rows)


def timestamp_micros() -> int:
    """Return the current time in microseconds since the epoch.

    Returns:
        The timestamp, as an integer.
    """
    return int(time.time() * 1_000_000)


def scan_user_events(
    instance_id: str,
    table_id: str,
    user_id: str,
) -> list[dict]:
    """Read every event for one user, across all salts.

    Because the salt is the key's first component, a single range scan
    cannot cover one user's events. This scans the whole table and
    filters client-side — the honest cost of salting, and the reason to
    use a separate index when this query is hot.

    Args:
        instance_id: The Bigtable instance id.
        table_id: The table id.
        user_id: The user to filter for.

    Returns:
        The matching rows, as dicts.
    """
    client = bigtable.Client(project="YOUR_PROJECT_ID")
    table = client.instance(instance_id).table(table_id)

    matches = []
    for row in table.read_rows():
        cells = row.cells
        cold = cells.get("cf-cold", {})
        if cold.get("user_id", [None])[0] == user_id:
            matches.append(
                {
                    "key": row.row_key.decode("utf-8"),
                    "event_type": cells.get("cf-hot", {}).get("event_type", [None])[0],
                    "region": cells.get("cf-hot", {}).get("region", [None])[0],
                    "amount": cold.get("amount", [None])[0],
                }
            )
    return matches


def scan_time_range(
    instance_id: str,
    table_id: str,
    start_ts: str,
    end_ts: str,
) -> list[dict]:
    """Scan every row whose key falls in a time range.

    The key layout is salt#user#timestamp#event, so a time range is not
    a contiguous range of keys unless you fix the salt. This function
    demonstrates the alternative key layout — timestamp first — where
    time-range scans are natural.

    Args:
        instance_id: The Bigtable instance id.
        table_id: The table id.
        start_ts: The inclusive start timestamp.
        end_ts: The inclusive end timestamp.

    Returns:
        The matching rows.
    """
    client = bigtable.Client(project="YOUR_PROJECT_ID")
    table = client.instance(instance_id).table(table_id)

    row_range = row_filters.RowRange(
        start_key=start_ts.encode("utf-8"),
        end_key=end_ts.encode("utf-8"),
    )
    results = []
    for row in table.read_rows(row_range=row_range):
        results.append({"key": row.row_key.decode("utf-8")})
    return results
```

The three functions together make the key-design trade-off concrete:

- `make_row_key` salts by user, which spreads a single user's writes across tablets.
- `scan_user_events` is then a **full-table scan with a client-side filter** — the cost you pay for that spreading.
- `scan_time_range` shows the opposite layout, where time ranges are contiguous.

**The engineering decision:** if a user's events are read constantly, put the salt *last* (`user#timestamp#salt#event`) so a user's rows stay contiguous, and accept that a single hot user creates one busy tablet. If writes dominate and reads are by time range, put the timestamp first.

### 3. Create a Firestore database and documents

```text
gcloud firestore databases create --location=nam5
```

```text
gcloud firestore indexes composite create --database='(default)' \
  --collection-group=events \
  --query-scope=collection \
  --field-config=field.path=region,field.order=ASCENDING \
  --field-config=field.path=event_ts,field.order=DESCENDING
```

Write documents with the client library, respecting the "read together, store together" rule:

```python
from google.cloud import firestore


def get_client() -> firestore.Client:
    """Return a Firestore client.

    Returns:
        The client.
    """
    return firestore.Client(project="YOUR_PROJECT_ID")


def upsert_user(client: firestore.Client, user_id: str, region: str) -> None:
    """Write one user document.

    The fields a read always needs are stored together, so reading the
    user is a single document read regardless of how many fields the
    document has.

    Args:
        client: The Firestore client.
        user_id: The user id.
        region: The user's region.
    """
    document = client.collection("users").document(user_id)
    document.set(
        {
            "region": region,
            "profile": {"channel": "web", "currency": "EUR"},
            "created_at": firestore.SERVER_TIMESTAMP,
        },
        merge=True,
    )


def append_order(client: firestore.Client, user_id: str, order: dict) -> None:
    """Append one order to a user's orders subcollection.

    Orders go in a subcollection rather than a field on the user
    document because the number of orders is unbounded and a Firestore
    document has a hard size limit of about 1 MiB.

    Args:
        client: The Firestore client.
        user_id: The user id.
        order: The order fields.
    """
    document = (
        client.collection("users")
        .document(user_id)
        .collection("orders")
        .document(order["order_id"])
    )
    document.set(
        {
            "event_ts": order["event_ts"],
            "event_type": order.get("event_type", "order"),
            "amount": order.get("amount", 0),
            "region": order.get("region", ""),
        }
    )


def read_user_with_orders(client: firestore.Client, user_id: str) -> dict:
    """Read a user and their orders.

    This is two document reads, because the orders live in a
    subcollection. If this read is on a hot path, the alternative is to
    denormalise a small number of recent orders onto the user document
    and keep the full history in the subcollection.

    Args:
        client: The Firestore client.
        user_id: The user id.

    Returns:
        A dict with the user fields and the list of orders.
    """
    user = client.collection("users").document(user_id).get().to_dict() or {}
    orders = [
        doc.to_dict()
        for doc in client.collection("users").document(user_id).collection("orders").stream()
    ]
    return {"user": user, "orders": orders}


def count_by_region(client: firestore.Client) -> dict:
    """Count events per region with a collection group query.

    A collection group query spans every `events` collection in the
    database, including subcollections.

    Args:
        client: The Firestore client.

    Returns:
        A dict of region -> count.
    """
    counts: dict[str, int] = {}
    query = client.collection_group("events").order_by("region")
    for document in query.stream():
        region = document.get("region", "UNKNOWN")
        counts[region] = counts.get(region, 0) + 1
    return counts
```

### 4. Create a Datastore kind and its composite index

```text
gcloud datastore indexes composite create \
    --project=YOUR_PROJECT_ID \
    --collection-namespace=orders \
    --property=region --property=event_ts \
    --kind=Order
```

```text
gcloud datastore indexes composite create \
    --project=YOUR_PROJECT_ID \
    --collection-namespace=orders \
    --property=event_type \
    --kind=Order \
    --non-interleaved
```

Write a non-key entity so the datastore assigns the ID:

```python
from google.cloud import datastore


def get_datastore_client() -> datastore.Client:
    """Return a Datastore client.

    Returns:
        The client.
    """
    return datastore.Client(project="YOUR_PROJECT_ID")


def create_order(
    client: datastore.Client,
    user_id: str,
    event_type: str,
    region: str,
    event_ts: str,
    amount: float,
) -> str:
    """Create one non-key Order entity.

    A non-key entity gets a server-assigned, monotonically increasing
    id, which gives chronological ordering for free but means the id
    cannot be chosen.

    Args:
        client: The Datastore client.
        user_id: The owning user.
        event_type: The event type.
        region: The region code.
        event_ts: The event timestamp.
        amount: The amount.

    Returns:
        The allocated entity id.
    """
    key = client.key("Order")
    entity = datastore.Entity(key=key)
    entity["user_id"] = user_id
    entity["event_type"] = event_type
    entity["region"] = region
    entity["event_ts"] = event_ts
    entity["amount"] = amount
    entity["created_at"] = datastore.datetime.now(datetime.timezone.utc)
    client.put(entity)
    return key.id()


def query_orders_by_region_and_time(
    client: datastore.Client,
    region: str,
    after: str,
) -> list[dict]:
    """Query orders by region and time, using the composite index.

    This query needs the composite index on (region, event_ts) that was
    created above. Without it, Datastore rejects the query with
    "The query requires a composite index".

    Args:
        client: The Datastore client.
        region: The region to filter on.
        after: The exclusive lower bound on event_ts.

    Returns:
        The matching entities, as dicts.
    """
    query = client.query(kind="Order")
    query.add_filter(filter=datastore.query.PropertyFilter("region", "==", region))
    query.add_filter(filter=datastore.query.PropertyFilter("event_ts", ">", after))
    query.add_order("event_ts")
    return [dict(entity) for entity in query.fetch()]
```

### 5. Create Memorystore instances and compare the APIs

```text
gcloud redis instances create cache-redis \
    --region=us-central1 \
    --size=1 \
    --tier=STANDARD_HA \
    --redis-version=REDIS_7_0

gcloud memcache instances create cache-memcached \
    --region=us-central1 \
    --size=1 \
    --tier=STANDARD_HA
```

Compare what you can do with the two, from the same client library:

```python
import redis


def exercise_redis(host: str, port: int = 6379) -> dict:
    """Exercise the Redis-only features.

    Args:
        host: The instance's IP address.
        port: The port.

    Returns:
        A dict of the results.
    """
    client = redis.Redis(host=host, port=port, decode_responses=True)
    results = {}

    # A plain string — Memcached can do this too.
    client.set("greeting", "hello", ex=300)
    results["string"] = client.get("greeting")

    # A hash — Memcached cannot do this.
    client.hset("user:u000914", mapping={"region": "AMER", "channel": "web"})
    results["hash"] = client.hgetall("user:u000914")

    # An atomic counter — Memcached's increment only works on strings.
    client.set("counter:events", 0)
    results["counter"] = client.incrby("counter:events", 4800)

    # A sorted set — a leaderboard.
    client.zadd("top:regions", {"AMER": 1238, "APAC": 1159, "EMEA": 1176})
    results["sorted_set"] = client.zrevrange("top:regions", 0, 2, withscores=True)

    # TTL inspection — the cache's most important operational property.
    results["ttl"] = client.ttl("greeting")

    return results


def exercise_memcached(host: str, port: int = 11211) -> dict:
    """Exercise the Memcached-only feature set.

    Args:
        host: The instance's IP address.
        port: The port.

    Returns:
        A dict of the results.
    """
    import memcache

    client = memcache.Client([f"{host}:{port}"])
    client.set("greeting", "hello", time=300)
    client.set("counter:events", 4800)

    return {
        "string": client.get("greeting"),
        "counter": client.incr("counter:events", 1),
        "stats": client.get_stats(),
    }
```

The contrast is stark: Redis gives you hashes, sorted sets, atomic increments on arbitrary keys, and streams. Memcached gives you a string map with an increment. That is the whole decision.

### 6. Price the four services

```python
import sys

sys.path.insert(0, "project/core")

from cost_model import estimate

HOURS_PER_MONTH = 730


def price_all(storage_gb: float = 500.0) -> dict:
    """Price the NoSQL options in the chapter.

    Args:
        storage_gb: The GB of data stored.

    Returns:
        A dict of service -> monthly cost.
    """
    return {
        "bigtable": round(
            estimate(
                "bigtable",
                node_gb=storage_gb * HOURS_PER_MONTH,
                monthly=True,
                apply_free_tier=False,
            ).total,
            2,
        ),
        "memorystore": round(
            estimate(
                "memorystore",
                gb_months=storage_gb * HOURS_PER_MONTH,
                monthly=True,
                apply_free_tier=False,
            ).total,
            2,
        ),
        "spanner": round(
            estimate(
                "cloud-spanner",
                nodes=3 * HOURS_PER_MONTH,
                processing_units=100 * HOURS_PER_MONTH,
                monthly=True,
                apply_free_tier=False,
            ).total,
            2,
        ),
    }


if __name__ == "__main__":
    for service, cost in price_all().items():
        print(f"{service:<15} ${cost:>10.2f}/mo")
```

---

## 🛠️ Common Errors and Fixes

### 1. `InvalidArgument: Cannot create column family` — adding a family after creation

```text
google.api_core.exceptions.InvalidArgument: Cannot create column family 'cf-extra' in table 'events'. Column families can only be created at table creation time.
```

Bigtable column families are fixed at table creation. To change the set, you **clone the table**:

```text
gcloud bigtable tables create events-bt.events-v2 \
    --column-families=cf-hot,cf-cold,cf-extra \
    --granularity=MILLISECONDS

gcloud bigtable tables copy events-bt.events events-bt.events-v2
```

The copy is a full data migration. This is exactly why the convention of "one family per access pattern, named for the pattern" exists: you decide the families up front, because changing your mind later is expensive.

### 2. `DeadlineExceeded` or a very slow scan on a Bigtable table

```text
google.api_core.exceptions.DeadlineExceeded: 504 Deadline exceeded after 60s
```

A scan that reads the whole table to find one user's rows is the classic symptom. It is not a bug in the client — it is the consequence of a **salted key**: the salt is the first component, so the user's rows are scattered across the entire key space, and a filter on `user_id` cannot prune tablets.

Two fixes:

- **Change the key layout** so the query is a prefix range: `user_id#timestamp#event_id`. You lose even write distribution but gain a contiguous range scan.
- **Add a second table** as an index: `user_index` keyed by `user_id#event_ts` pointing at the primary row key. Writes to both tables go in the same batch mutation, so they are consistent.

The operational rule: **if a query is frequent, it must be a key range, not a filter.** Bigtable filters are applied server-side after reading the rows, so a filter never reduces IO the way a range scan does.

### 3. `BadRequest: The query requires a composite index`

```text
google.api_core.exceptions.BadRequest: 400 The query requires a composite index.
```

This is the Datastore and Firestore composite-index error. The index must mirror the query's shape exactly: **equality-filtered properties first, then the inequality-filtered property, then the sort orders.**

```text
gcloud datastore indexes composite create \
    --collection-namespace=orders \
    --property=region \
    --property=event_ts \
    --kind=Order
```

For Firestore, the same error appears with a link in the message:

```text
google.api_core.exceptions.FailedPrecondition: 400 The query requires a composite index.
```

Create it from the console (the error message links to a pre-filled creation form) or with `gcloud firestore indexes composite create`. **Indexes take a minute or two to build** — the query fails until they are ready.

### 4. `ReadError` / stale reads on Datastore after a write

```text
google.api_core.exceptions.NotFound: 404 no matching entity found
```

or, more insidiously, the write succeeds and the read returns the *previous* value.

This is the eventual-consistency behaviour of a **non-ancestor query**. The write was committed to one datastore group and has not yet propagated to the replica serving your read.

The fix depends on what you actually need:

- **You need to read your own write** → use an **ancestor query** (strongly consistent), give the entity a parent, and query with `ancestor=Key(...)`. Or use a **key lookup**, which is strongly consistent.
- **You need strong consistency without restructuring** → use a strong read: `query.fetch(..., read_consistency=datastore.query.ReadConsistency.STRONG)` at the cost of latency and availability.
- **You need "read your own write" within one entity group** → put the child entities under a parent (an ancestor path). This is the standard pattern for aggregates.

The Firestore equivalent is simpler: **a document read is always strongly consistent.** If you are hitting stale reads in Firestore, you are probably reading via a `collectionGroup` query against an aggregated document that is written by a different process.

### 5. `FireStore` write succeeds but the subcollection data is orphaned

```text
# After client.collection("users").document(user_id).delete()
# the orders subcollection still exists and is still readable:
orders = list(client.collection("users").document(user_id).collection("orders").stream())
```

This is not an error; it is Firestore's documented behaviour. **Deleting a document does not delete its subcollections.** The fix is to delete the subcollections explicitly, in the right order (children before the parent), and to make the deletion idempotent:

```python
def delete_user(client, user_id: str) -> int:
    """Delete a user and every subcollection beneath it.

    Firestore does not cascade-delete subcollections, so the caller
    must do it. The order matters: children first, then the parent.

    Args:
        client: The Firestore client.
        user_id: The user id.

    Returns:
        The number of documents deleted.
    """
    deleted = 0
    user_ref = client.collection("users").document(user_id)
    for collection_name in ("orders", "preferences", "devices"):
        for doc in user_ref.collection(collection_name).stream():
            doc.reference.delete()
            deleted += 1
    user_ref.delete()
    return deleted + 1
```

### 6. `OOM command not allowed` or `OOM` on a Memorystore instance

```text
OOM command not allowed when used memory > 'maxmemory' setting.
```

Redis rejects a write that would exceed `maxmemory`. This is a feature — it protects the instance from accepting writes it cannot serve — but it means a cache that grows without a TTL will start rejecting writes, and your application will see errors where it expected success.

The fix is on the data, not the instance:

- **Set TTLs on every key.** A cache without TTLs is a memory leak with extra steps. `client.set(key, value, ex=300)`.
- **Use `maxmemory-policy allkeys-lru`** so the instance evicts the least-recently-used keys rather than rejecting writes. Memorystore's `STANDARD_HA` tier supports this via `gcloud redis instances update --redis-config maxmemory-policy=allkeys-lru`.
- **Size the instance for the working set, not the total dataset.** A cache holding 10 GB of data in a 1 GB instance is a configuration error, not a capacity problem.

---

## 💡 Production Notes

- **Treat the Bigtable row key as a schema migration.** You cannot change it without rewriting the table. Write a design document that specifies the key, the salt strategy, and the expected query patterns *before* you write the first row, and review it against the row-key checklist: is it unique? does it spread writes? does it make the hottest query a contiguous range scan? can old data be dropped by prefix?
- **Never rely on a Bigtable filter for a hot query.** A filter reads the rows and then discards them server-side; it does not reduce IO. Every hot query must be a row-key range scan or a point lookup, backed by a secondary index table if necessary.
- **Use one column family per access pattern and set the storage type accordingly.** `cf-hot` on SSD, `cf-cold` on HDD. Bigtable's replication and garbage collection are per-family, so a family that is written once and read never (an archive family) should have a TTL and an HDD backing.
- **Datastore's eventual consistency is not a detail — it is a design constraint.** If the application must read its own writes, use ancestor queries or key lookups, and model the entity hierarchy to make the common queries ancestor queries. Non-ancestor queries are for dashboards and batch reads only.
- **In Firestore, put data that is read together in the same document.** A document read is one operation regardless of field count, and it is one billing unit. Splitting a user's profile across a document and a subcollection doubles the read cost of every profile fetch. Split only when the child is unbounded or has a different access pattern.
- **Never let a Firestore subcollection outlive its parent without a plan.** Deleting a user document leaves the subcollection behind — still stored, still billable, and still readable by anyone with path-level permission. Delete children first, and make the whole operation idempotent.
- **Use Firestore transactions or `FieldValue.increment()` for anything two clients can write.** Firestore resolves offline conflicts with last-write-wins per document, so a client-side read-modify-write of a counter silently loses updates. The server-side atomic operations are the only safe way to do concurrent updates.
- **Give every Redis key a TTL and set `maxmemory-policy=allkeys-lru`.** A cache that can exceed its memory limit will start rejecting writes, and your application will surface those rejections as errors in the wrong place. The TTL is the primary defence; the eviction policy is the backstop.
- **Prefer Redis to Memcached unless you are certain you only need a flat string map.** The migration Memcached → Redis is trivial; Redis → Memcached is not. Memorystore prices them comparably for the same size, so the extra capability is close to free insurance.

---

## 🔑 Key Takeaways

- Four NoSQL models, four different trades: key-value (speed), wide-column (scale with sparse columns), document (natural aggregates), graph (traversal). **The access pattern picks the model.**
- **Bigtable is a sparse, sorted, multi-dimensional map.** Rows are sorted by key, columns are sparse, and a **column family is the unit of physical configuration** — storage type, replication, garbage collection, and TTL.
- **The row key is the Bigtable schema.** Salting spreads writes but destroys range-scan locality; a timestamp-first key gives time-range scans but creates a permanent hotspot. Splitting is at the median, so skew is not fixed automatically.
- **Filters never reduce Bigtable IO.** A hot query must be a row-key range scan or a point lookup, with a secondary index table when the access pattern does not match the key.
- **Datastore's key vs non-key entity distinction changes the ID semantics**: key entities let you choose the ID; non-key entities get a server-assigned monotonically increasing ID, which gives chronological ordering for free.
- **Datastore non-ancestor queries are eventually consistent.** Ancestor queries and key lookups are strongly consistent. This is an architectural constraint, not a rounding error.
- **Firestore's rules:** data read together goes in one document; unbounded children go in a subcollection; **deleting a parent does not delete its subcollections**; offline conflicts resolve last-write-wins per document, so concurrent updates need server-side atomic operations.
- **Redis vs Memcached:** Memcached is a flat string map with no persistence, no replication, no failover. Redis adds data structures, persistence, replication with failover, atomic counters, and streams. Choose Redis unless you are certain you need only a string map.
- **Memorystore is regional.** A global cache needs a per-region instance plus routing, or a different service.

---

## 📚 Practice Exercises

1. **Design the Bigtable key for the course pipeline.** The course events have `event_id`, `user_id`, `event_ts`, `event_type`, `region`, `channel`, `currency`, `amount` (from `pipeline_logic.EVENT_FIELDS`). Produce four candidate row keys — salted-user-first, user-first, timestamp-first, and time-bucketed — and for each, state: (a) the write distribution, (b) which query is a contiguous range scan, (c) whether a hot key is possible, and (d) how you would expire old data. Then pick one and justify it against the pipeline's actual queries: the summary aggregation (a scan over everything) and the per-user lookup.
2. **Model the salting trade-off.** Write a simulator that takes N events with the course's actual distribution (4,800 events across 4,800 distinct users per `sample_data/events.csv`) and applies a row-key function, then reports: the number of distinct tablets touched, the maximum rows per tablet, and the number of tablets that would be touched by a per-user query. Compare salted and unsalted keys. The number of tablets touched by the per-user query is the metric that quantifies the cost of salting — make it explicit.
3. **Verify the Firestore/Datastore consistency rules.** Write a module under `project/core/` with two functions: `firestore_read_cost(field_count, doc_count)` and `datastore_read_consistency(query_type)` returning `"strong"` or `"eventual"`. Then write a short document (as a Python docstring) stating, for each of Datastore's three query types — key lookup, ancestor query, non-ancestor query — whether it is strongly consistent and what that means for read-your-writes. Tie the answer to the course's `pipeline_logic.deduplicate()` and the question "did my load land?"
4. **Compare Redis and Memcached feature-by-feature.** Write a table-driven comparison in code: a list of capability dicts for each service, and a function that scores a workload's requirements against them. Model three workloads — (a) a session cache keyed by session id with a 30-minute TTL, (b) a rate limiter using a sliding window, (c) a leaderboard — and have the function recommend a service for each with a reason. The rate limiter and the leaderboard must both come out as Redis, and the reason must cite a specific data structure.
5. **Choose the right service for five workloads.** For each of: (a) a clickstream archive of 50 TB written once and read monthly, (b) a per-user session store with 1 ms reads and 100k keys/second, (c) a mobile app's offline-synced user profile, (d) a global transaction ledger with strict serialisability, (e) an application cache in front of Cloud SQL — pick one of Bigtable, Datastore, Firestore, Spanner, Memorystore, Cloud SQL, or BigQuery, and write the reason in terms of the access pattern. Check your answers against `service_catalog.get_service(id).data_role` and explain any mismatch between the catalogue's role and your choice.
6. **Implement the Datastore composite index rule.** Write a function `needs_composite_index(filters, orders)` that returns True when a query requires an explicit composite index, using the real rule: more than one property with an equality filter, plus an inequality filter or an order by on a different property. Test it against four query shapes: single equality; equality plus equality; equality plus inequality; equality plus order-by. Then write the `gcloud datastore indexes composite create` command for the case that needs one.
7. **Price a Bigtable table with a hot key.** Use `estimate("bigtable", node_gb=...)` to price a table with 5 TB of data. Then model the hot-key case: 1% of writes hit one row key, so that tablet's server cannot be scaled independently. Explain in prose why Bigtable's median-based splitting does not fix this, and describe the mitigation the service provides (hot splitting) and its limits. Then state what you would change in the key design to avoid it.

---

## 📖 Further Reading

- [Cloud Bigtable documentation](https://cloud.google.com/bigtable/docs) — the service overview and concepts
- [Bigtable data model](https://cloud.google.com/bigtable/docs/data-model) — rows, column families, cells, and timestamps
- [Bigtable row key design](https://cloud.google.com/bigtable/docs/row-key-design) — salting, key rotation, and the anti-patterns
- [Datastore indexes](https://cloud.google.com/datastore/docs/indexes) — automatic and composite indexes, and the exact composite-index rule
- [Datastore consistency](https://cloud.google.com/datastore/docs/articles/balancing-strong-and-eventual-consistency-with-google-cloud-datastore) — ancestor vs non-ancestor semantics
- [Firestore data model](https://cloud.google.com/firestore/docs/data-model) — documents, collections, subcollections, and the 1 MiB limit
- [Firestore queries and indexes](https://cloud.google.com/firestore/docs/query-data/indexing) — index requirements and collection group queries
- [Memorystore for Redis and Memcached](https://cloud.google.com/memorystore/docs) — the two products, their tiers, and their limits
