# Design: Job Scheduler (cron + DAG)

## 1. Requirements

### Functional
- Define jobs of three kinds:
  - `once`  – run once at a specific time (`run_at`).
  - `cron`  – run repeatedly with a fixed period (`interval_seconds`)
             anchored at the previous successful run.
  - `dag`   – a directed acyclic graph of child jobs; the parent
             "run" is just an ordered execution of the children
             once their dependencies succeed.
- A worker thread polls the job store, dispatches due jobs, and writes
  a `Run` record per execution.
- Manual trigger: `POST /api/jobs/{id}/run` enqueues an immediate run.
- API to inspect jobs, runs, and run results.
- Persisted job and run state (JSON on disk).

### Non-functional
- Mockable time source so tests can advance the clock without sleeping.
- Bounded growth of run history per job (keep the last N runs).
- Single-process; in-memory + JSON-on-disk.

## 2. Capacity

For the laptop demo: 1 worker, polling every 100 ms, holding up to
10 000 active jobs. Each tick scans the index of `due` jobs; in
practice the index is small because we sort by `next_run_at` and
pop from the head.

Production scale-out:
- A durable priority queue (Kafka / SQS / Redis ZSET) keyed by
  `next_run_at`, polled by N workers.
- Leader election so a job is not double-dispatched.
- Persistent run log in a column store.

## 3. High-level architecture

```
client --> Flask app.py
                |
                v
        +--------------------+
        |  JobScheduler svc  |
        +-----+----------+---+
              |          |
   +----------+          +----------+
   v                                v
KeyValueStore (jobs, runs)     worker thread
                                       |
                                       v
                              _execute_job -> JobRunner
                                       |
                          +------------+------------+
                          v            v            v
                     FunctionJob  ShellJob    DAGJob
```

## 4. API

| Method | Path                       | Body                                                | Response          |
|--------|----------------------------|-----------------------------------------------------|-------------------|
| POST   | `/api/jobs`                | `{"name", "kind": "once\|cron\|dag", ...}`          | `Job`             |
| GET    | `/api/jobs`                | —                                                   | list of `Job`     |
| GET    | `/api/jobs/{id}`           | —                                                   | `Job`             |
| POST   | `/api/jobs/{id}/run`       | `{}`                                                | `Run`             |
| GET    | `/api/runs`                | `?job_id=&limit=`                                   | list of `Run`     |
| GET    | `/api/runs/{id}`           | —                                                   | `Run`             |
| GET    | `/health`                  | —                                                   | `{ok}`            |
| GET    | `/metrics`                 | —                                                   | text              |

### Job payload by kind

```jsonc
// once
{ "name": "send_email", "kind": "once", "run_at": 1700000000.0,
  "payload": {"to": "x@y.com"} }

// cron
{ "name": "ping", "kind": "cron", "interval_seconds": 60,
  "payload": {} }

// dag
{ "name": "etl", "kind": "dag",
  "children": [
    { "name": "extract", "kind": "once", "run_at": <now>,
      "payload": {} },
    { "name": "transform", "kind": "once",
      "depends_on": ["extract"], "payload": {} }
  ] }
```

## 5. Data model

`KeyValueStore` (json on disk):

- `job:{job_id}` -> `{job_id, name, kind, status, payload, ...}`
- `jobindex:all` -> [job_id, ...]
- `run:{run_id}` -> `{run_id, job_id, started_at, finished_at,
                     status, result, error, attempt}`
- `runindex:job:{job_id}` -> [run_id, ...]   (capped at 200)
- `due` -> sorted list of `(next_run_at, job_id)` reconstructed at
  load; we keep an in-memory priority queue for dispatch.

In memory: `_due: list[(next_run_at, job_id)]` (a sorted list, popped
from the head on each tick). A heap is overkill for 10k entries.

## 6. Read / write paths

### Write (create job)
1. Validate kind, payload, and cron `interval_seconds > 0`.
2. Persist under `job:{id}`. Append to `jobindex:all`.
3. Compute `next_run_at` and insert into the in-memory due list.
4. For `dag` jobs, also persist child jobs and link them.

### Worker tick
1. Pop any jobs whose `next_run_at <= now()`.
2. Create a `Run` (status `running`).
3. Invoke the runner for the job's kind.
4. On success: persist the result, mark `Run.status=success`, and
   reschedule the next run for `cron` jobs.
5. On failure: `Run.status=failed`, exponential backoff up to
   `max_retries`. A `cron` job continues ticking even when a
   particular run fails.

### Manual trigger
- `POST /api/jobs/{id}/run` records a `Run` with `trigger=manual`
  and runs synchronously (returns the final result). The cron
  cadence is unaffected.

## 7. Failure modes

| Failure                 | Handling                                                       |
|-------------------------|----------------------------------------------------------------|
| Runner raises           | `Run.status=failed`, exponential backoff per-job (`max_retries`) |
| Process crash mid-run   | on startup we mark all `running` runs as `failed`              |
| Clock skew              | tests inject a `time_fn`; production uses monotonic `time.time`|
| DAG cycle               | reject on submit; cycle detection is a single DFS              |
| Overdue cron            | we coalesce missed ticks into a single run at recovery         |

## 8. Tradeoffs

- **Sorted list vs heap:** list is fine up to ~10k jobs; heap beats it
  beyond.
- **Synchronous vs async runs:** synchronous via the worker thread is
  the simplest demonstration. For long jobs, swap the runner for a
  thread pool.
- **Single worker:** avoids double-dispatch in this demo. In
  production, leader election or a leased queue is required.
- **Run retention:** cap per job to keep the store bounded.

## 9. Code map

- `code/service.py` — `JobScheduler`, `JobRunner`s, due-list logic.
- `code/app.py`     — Flask HTTP layer.
- `tests/test_service.py` — 6+ tests using an injected clock.
- `tests/test_app.py`     — 5+ HTTP tests.
