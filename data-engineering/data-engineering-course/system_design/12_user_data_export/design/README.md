# Design: User Data Export (async download pipeline)

## 1. Requirements

### Functional
- User clicks "Download my data". The server returns immediately with
  an export job ID; the user polls the job and downloads a file when
  it's ready. This is the standard GDPR / "data portability" flow.
- `POST /api/exports` accepts a `user_id` and creates an export.
  Status goes `QUEUED → RUNNING → READY → EXPIRED`.
- `GET /api/exports/{id}` returns the export metadata + status.
- `GET /api/exports/{id}/download` returns the JSON blob (or 410
  Gone once expired).
- The export pipeline:
  1. Reads data from a configurable set of "collections"
     (e.g. `users`, `orders`, `activity`, `preferences`).
  2. Builds a single JSON document.
  3. Stores it under a blob URL.
- Persistence: export state survives process restarts; in-flight
  exports are picked up on startup.

### Non-functional
- Single-process worker, in-memory + JSON-on-disk.
- Expiry: an export is `EXPIRED` after `ttl_seconds` (default 24h).
  Once expired, the underlying blob is freed.
- Bounded blob size: 10 MB cap; rejected at submission if user
  has too much data.

## 2. Capacity

For a laptop demo: 1 worker thread, blobs up to 10 MB on disk under
`var/blobs/`, exports retained for 24h. In production this would
be a streaming pipeline (Kafka / S3 / Spark) with object-store
expiry via lifecycle rules.

## 3. High-level architecture

```
                POST /api/exports
                       |
                       v
                +------------------+
                |  ExportService   |
                +---------+--------+
                          | enqueue
                          v
                +------------------+
                |  worker thread   |
                +---------+--------+
                          | gather -> compile -> write blob
                          v
                +------------------+
                |   BlobStore      |  (file-backed)
                +------------------+
                          ^
                          |
                GET /api/exports/{id}/download  --> returns blob bytes
```

## 4. API

| Method | Path                                | Body / Response                                |
|--------|-------------------------------------|------------------------------------------------|
| POST   | `/api/exports`                      | `{"user_id": "u-1"}`                           |
| GET    | `/api/exports/<id>`                 | `{id, user_id, status, created_at, ...}`       |
| GET    | `/api/exports/<id>/download`        | JSON document (200) or 410 Gone                |
| GET    | `/api/exports?user_id=u-1`          | list of exports for a user                     |
| GET    | `/health`                           | `{ok, ts}`                                     |
| GET    | `/metrics`                          | Prometheus text                                |

## 5. Data model

`KeyValueStore` (json on disk):

- `export:{export_id}` -> `{export_id, user_id, status, created_at,
                           started_at, finished_at, expires_at,
                           size_bytes, error, collections}`
- `exportindex:user:{user_id}` -> [export_id, ...]
- `exportindex:all` -> [export_id, ...]

Blobs:

- `var/blobs/{export_id}.json` — the actual compiled export.

Collections: registered `Collection` objects that know how to read
a slice of user data. Built-in collections are
`UserProfileCollection`, `OrdersCollection`, `ActivityCollection`,
`PreferencesCollection`.

## 6. Read / write paths

### Write (create export)
1. Validate `user_id` (non-empty string).
2. Create `Export` with `status=QUEUED`, persist.
3. Wake the worker.

### Worker tick
1. Pop the oldest `QUEUED` export.
2. Set `status=RUNNING`, `started_at=now`.
3. For each registered collection, call `collect(user_id)`. If the
   result exceeds the per-export cap, mark `status=FAILED`.
4. Compile into `{meta: {...}, data: {coll: [...]}}`.
5. Write to a blob file. Set `status=READY`, `finished_at=now`,
   `expires_at=now + ttl_seconds`.

### Read
- `GET /api/exports/{id}` — read metadata.
- `GET /api/exports/{id}/download` — read blob; if `status=EXPIRED`
  or `finished_at + ttl < now`, return 410. Otherwise stream the
  JSON.

### Expiry sweep
- Every worker tick, any `READY` exports past `expires_at` are
  moved to `EXPIRED` and their blob files are deleted.

## 7. Failure modes

| Failure                   | Handling                                          |
|---------------------------|---------------------------------------------------|
| User has too much data    | mark `FAILED`, store error message                |
| Collection raises         | mark `FAILED` with the collection name            |
| Disk write fails          | mark `FAILED`, retry once on next tick            |
| Process crash mid-export  | on startup, all `RUNNING` exports go back to `QUEUED` |
| Blob fetch after expiry   | 410 Gone; the export metadata is still readable   |

## 8. Tradeoffs

- **Per-user export vs. bulk export** — we keep the simpler per-user
  shape; a "team export" could be a DAG of per-user jobs.
- **Inline JSON vs. streaming** — inline is fine for the demo; for
  large exports we'd stream from disk with a Content-Disposition.
- **Synchronous /api/exports** — we always return a job id; the
  caller polls. This decouples HTTP latency from data volume.
- **Single worker** — for higher throughput, fan out the queue to
  N workers with leader election.

## 9. Code map

- `code/service.py` — `ExportService`, `Collection` base, built-in
  collections, blob store, expiry sweep.
- `code/app.py`     — Flask HTTP layer.
- `tests/test_service.py` — 6+ service tests.
- `tests/test_app.py`     — 5+ HTTP tests.
