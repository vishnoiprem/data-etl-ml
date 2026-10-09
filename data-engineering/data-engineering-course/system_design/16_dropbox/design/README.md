# 16 — Dropbox-style File Sync (chunking + dedup)

> **Lesson 16 of the Distributed Data Storage & Partitioning track**

A small Dropbox clone. Files are split into chunks (fixed-size 4 MB, with
optional content-defined chunking via Rabin-Karp fingerprints), each
chunk is SHA-256 hashed, deduped against a chunk store, and the file
metadata references the chunk list. Two users with the same photo use
the same chunk — disk is shared, only metadata is per-file.

---

## 1. Requirements

### Functional
- `POST /api/files` — upload a file (filename, base64 content); server
  chunks, dedupes, and persists.
- `GET /api/files/{id}/download` — reassemble from chunks.
- `GET /api/files` — list files (with metadata).
- `GET /api/chunks/{hash}` — fetch a single chunk (debug, dedup inspection).
- Content-defined chunking: split on content boundaries (Rabin-Karp) or
  fixed 4 MB windows.

### Non-functional
- **Dedup** — identical chunks across files stored once.
- **Streaming upload/download** — don't load entire file in memory for
  reassembly in real systems (we use in-memory here for the course).
- **Versioning** — every upload bumps `version` and `mtime`.
- **Idempotent chunks** — re-uploading a chunk is a no-op.

### Out of scope
- Delta sync (rsync-style rolling hash).
- Real chunk persistence to S3 (we use local blob store).
- Multi-user sharing / ACLs.

---

## 2. Capacity estimation

| Metric | Value |
|---|---|
| Avg file size | 50 MB |
| Chunk size | 4 MB (fixed) or 1–8 MB (CDC) |
| SHA-256 of chunk | 32 B |
| Metadata per file | ~200 B + N × 64 B |
| Dedup ratio | typical 30–60% |

A 1 PB corpus with 40% dedup → ~600 PB raw → ~360 PB on disk.

---

## 3. High-level design

```
   client ──► [ Flask ] ──► [ FileSyncService ]
                                │
                ┌───────────────┼──────────────────┐
                ▼                                  ▼
         [ chunker ]                          [ chunk store ]
         fixed-size or CDC                       │
         (Rabin-Karp)                            hash → blob
                │                                  │
                ▼                                  ▼
         [ chunks: list[(hash, size)] ]      [ var/chunks/ ] (disk)
                │
                ▼
         [ file metadata: id, name, chunks, version, mtime ]
                │
                ▼
         [ var/files.json ] (KeyValueStore)
```

- Chunkers: `FixedSizeChunker` and `RabinKarpChunker` (parameterized by
  `mask` and `min/max`).
- Chunk store: `var/chunks/<hash>` is written once. `KeyValueStore` keeps
  `chunk:<hash> → {size, refcount}`.
- File metadata: `file:<id> → {name, chunks, size, version, mtime}`.

---

## 4. API

| Method | Path | Body / Params | Returns |
|---|---|---|---|
| `POST`  | `/api/files` | `{"filename": "x.png", "content_b64": "..."}` | `{id, filename, size, version, chunks, dedup_ratio}` |
| `GET`   | `/api/files` | — | list of file metadata |
| `GET`   | `/api/files/{id}` | — | file metadata |
| `GET`   | `/api/files/{id}/download` | — | `{"filename", "content_b64"}` |
| `GET`   | `/api/chunks/{hash}` | — | base64-encoded chunk bytes |
| `GET`   | `/metrics` | — | counters |
| `GET`   | `/health` | — | `{"ok": true}` |

---

## 5. Data model

### Chunk record
```
chunk_store[hash] = {"size": int, "refcount": int}
```

### File record
```
file_store[id] = {
  "id": str,
  "filename": str,
  "size": int,        # raw byte size
  "chunk_size": int,  # nominal chunk size used
  "chunks": [{"hash": str, "size": int}],  # in order
  "version": int,
  "mtime": float,
  "uploaded_at": float,
}
```

### Chunker
- `FixedSizeChunker(size=4MB)` — slice by bytes.
- `RabinKarpChunker(...)` — window over the buffer, find positions where
  the rolling hash matches a mask, emit chunks. Default windows 1–8 MB.

---

## 6. Read path

`GET /api/files/{id}/download`:
1. Look up `file:<id>` in `file_store`.
2. For each chunk in `chunks`, fetch the bytes from chunk store.
3. Concatenate → base64.
4. Return `{filename, content_b64, size}`.

---

## 7. Write path

`POST /api/files`:
1. Decode `content_b64` → bytes.
2. Chunk: produce a list of (offset, length) windows.
3. For each window, compute SHA-256, look up chunk store.
   - existing → refcount++ (no-op write)
   - new → write to `var/chunks/<hash>`, refcount = 1
4. Persist file metadata. Bump `version` if filename reused (latest wins).
5. Return `{id, size, dedup_ratio = total_stored / raw_size}`.

---

## 8. Failure modes

| Failure | Mitigation |
|---|---|
| Chunk store corruption | In production: replication + checksums. Here: write to tmp + rename. |
| Duplicate filename | Latest version wins. Version counter increments. |
| Huge file | Bounded chunk size avoids single-blob blow-up. |
| Bad base64 | Reject with 400. |
| Disk full | Surface error; in production: queue / spill to S3. |

---

## 9. Tradeoffs

- **Fixed-size vs CDC**: fixed is simpler, CDC handles edits better (one
  byte change in a 1 GB file only re-uploads a few MB).
- **Chunk size 4 MB**: balances dedup granularity vs metadata overhead.
  Smaller → more dedup, more metadata. Larger → less dedup, less metadata.
- **Sync refcounts**: optional — needed only for accurate dedup stats.
- **Per-chunk vs whole-file hashing**: per-chunk dedup is the entire point.
  Without it, you have a glorified blob store.

---

## 10. How the code maps to this design

| File | Role |
|---|---|
| `code/service.py` | `FixedSizeChunker`, `RabinKarpChunker`, `ChunkStore`, `FileSyncService`. |
| `code/app.py` | Flask HTTP service. |
| `tests/test_service.py` | Chunkers, dedup, upload/download roundtrip. |
| `tests/test_app.py` | HTTP-level tests. |
