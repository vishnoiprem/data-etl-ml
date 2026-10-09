# 23 — Document Processing Pipeline

An asynchronous pipeline that turns uploaded documents into indexed
extracted entities. The state machine is:

```
   UPLOADED ──parse──▶ PARSED ──extract──▶ EXTRACTED ──index──▶ INDEXED
```

A background worker thread drives transitions. The HTTP API is the
control plane: upload, poll status, query entities, search.

## Requirements

### Functional
- Upload a document (`content`, `type`) → returns `doc_id`, status `UPLOADED`.
- Get document by id: returns status, parsed text, extracted entities.
- Get entities only: `GET /api/documents/{id}/entities`.
- Search across indexed documents by substring: `GET /api/search?q=`.
- Background worker advances state. Status reflects current state.

### Non-functional
- Worker is non-blocking; transitions are observable in real time.
- In-memory persistence, no external queue.

## Capacity

| Dimension | Assumption |
| --- | --- |
| Docs ingested/day | 100k |
| Avg doc size | 50 KB text |
| Pipeline stages | 3 (parse, extract, index) |
| Search QPS | 50 |
| Worker tick | 200ms |

## High-level architecture

```
client ──POST /api/documents──▶ DocService
                                    │
                                    ▼
                              ┌──────────┐
                              │ UPLOADED │  ───┐
                              └──────────┘     │ worker tick
                                    │          │ advances any doc
                                    ▼          │ that has done its
                              ┌──────────┐     │ previous stage
                              │  PARSED  │ ────┘
                              └──────────┘
                                    │
                                    ▼
                              ┌──────────┐
                              │EXTRACTED │
                              └──────────┘
                                    │
                                    ▼
                              ┌──────────┐
                              │ INDEXED  │
                              └──────────┘
```

The worker is a daemon thread started in the service constructor. It
ticks every `WORKER_TICK_S` and processes the next doc in `UPLOADED` →
`PARSED` → `EXTRACTED` → `INDEXED`. Each stage calls a pluggable
function (`parse_fn`, `extract_fn`, `index_fn`) — production would wire
Tesseract / spaCy / Elastic here.

## API

| Method | Path | Description |
| --- | --- | --- |
| POST | `/api/documents` | Upload. Body: `{content, type}`. |
| GET  | `/api/documents/{id}` | Status + parsed text + entities. |
| GET  | `/api/documents/{id}/entities` | Entities only. |
| GET  | `/api/search?q=` | Substring search across INDEXED docs. |
| GET  | `/health` | Liveness + worker state. |

## Data model

```
kv["doc:<id>"] -> {
  "id": str,
  "type": str,
  "content": str,
  "status": "UPLOADED|PARSED|EXTRACTED|INDEXED",
  "parsed_text": str,
  "entities": [ {type, value}, ... ],
  "indexed_at_ms": int,
  "uploaded_at_ms": int,
}
kv["docs:index"] -> [id, ...]                  # ordered by upload time
kv["search:term:<token>"] -> [doc_id, ...]     # inverted-ish, capped
```

We keep an inverted token index (lowercase, alpha tokens) to make
`/api/search` cheap. Substring search is implemented as OR over token
matches.

## Read / Write paths

**Upload**:
1. Generate `doc_id` (Snowflake as string).
2. Persist `doc` with status `UPLOADED`.
3. Append id to `docs:index`.

**Worker tick**:
1. Find next non-terminal doc.
2. Run current-stage function (parse / extract / index).
3. Persist updated record.
4. Sleep until next tick.

**Search**:
1. Tokenize `q` on whitespace.
2. Union the doc-id lists for each token.
3. Filter to INDEXED docs and apply substring over content as a fallback.

## Failure modes

| Failure | Mitigation |
| --- | --- |
| Worker not running | Service starts it in `__init__`; `/health` shows worker state. |
| Parse fails on a doc | Status moves to `FAILED` (terminal). Real systems dead-letter. |
| Search corpus explodes | We cap the inverted index per token to 1k doc ids. |
| Worker dies | Tests can disable worker via flag. |

## Tradeoffs

- **One worker thread** keeps this simple; production would scale by
  sharding docs across N workers and using a real queue.
- **In-memory persistence** means restart loses data. Production would
  push to S3 + Postgres.
- **Stages are sync within the worker** to keep the example readable;
  a real system fans each stage out to its own worker pool.

## Code map

- `code/service.py` — `DocumentService` + state machine + worker.
- `code/app.py` — Flask HTTP.
- `tests/test_service.py` — service tests.
- `tests/test_app.py` — HTTP tests.
