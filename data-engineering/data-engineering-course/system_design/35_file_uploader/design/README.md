# 35 — File Uploader for an AI Chat App (Chunked, Resumable)

> **Module 3 of 6 — Agentic AI Systems**

A complete, runnable design + implementation of a chunked, resumable
file uploader. AI chat apps need this so users can attach PDFs, images,
and CSVs to conversations and have them survive flaky mobile networks.

The flow mirrors S3 multipart uploads and the `tus.io` protocol:

```
client ──► /initiate         ◄── {upload_id, chunk_size}
        ──► PUT /chunks/<idx>×N  (binary, can retry)
        ──► GET /status       ◄── {received, missing}     (resume)
        ──► POST /complete    ◄── {file_id, sha256, size}
        ──► GET /files/<id>/download
```

---

## 1. Requirements

### Functional
- Initiate an upload with `{filename, size, content_type, chunk_size?}`.
- Accept binary chunk uploads `PUT /uploads/<id>/chunks/<idx>`.
- Expose a status endpoint so clients can resume.
- Concatenate chunks on `complete`; produce a `file_id` and SHA-256.
- Download a completed file by `file_id`.
- Abort an in-progress upload.

### Non-functional
- **Resumable**: client can re-issue the missing chunks.
- **Idempotent**: re-sending the same chunk is harmless.
- **Bounded memory**: chunks are streamed to disk, not held in RAM.
- **Safe**: reject path traversal, oversize files, and bad content types.

### Out of scope
- Direct S3/GCS backend (we use the local FS).
- Server-side antivirus / DLP scanning.

---

## 2. Capacity estimation

| Metric | Value |
|---|---|
| Max file size | 2 GB |
| Default chunk size | 256 KB |
| Chunks per 2 GB file | 8 K |
| Concurrency per upload | ~4 in-flight chunks |
| Storage | FS-backed, one file per chunk + final stitched file |

The dominant engineering cost is **disk I/O on `/complete`** (a single
sequential 2 GB write). In production this is replaced by an S3
"complete multipart upload" call.

---

## 3. High-level design

```
        ┌─────────────────────────────────────┐
client ─┤ initiate / chunks / status / etc.   │
        └──────────────┬──────────────────────┘
                       │ KV metadata
                       ▼
              ┌─────────────────┐
              │  upload state   │  upload:<id>     {filename, size,
              │  (KeyValueStore)│                  chunk_size, received[]}
              └─────────────────┘
                       │
                       │ on complete
                       ▼
   var/uploads/<id>/<idx> ──stitch──► var/files/<file_id>
```

State machine for an upload:

```
                    initiate
                       │
                       ▼
                 ┌──────────┐
                 │initiated │──put_chunk──►┌────────────┐
                 └──────────┘              │ in_progress│
                                           └─────┬──────┘
                                                 │ complete
                                                 ▼
                                          ┌────────────┐
                                          │ completed  │  (file_id set)
                                          └────────────┘
                                                 │
                          abort (from any non-terminal state) ──► aborted
```

---

## 4. API

| Method | Path | Body | Returns |
|---|---|---|---|
| `POST` | `/api/uploads/initiate` | `{filename, size, content_type, user_id?, chunk_size?}` | `Upload` |
| `PUT`  | `/api/uploads/<id>/chunks/<idx>` | raw bytes | `{ok, idx, bytes}` |
| `GET`  | `/api/uploads/<id>/status` | — | `{received, missing, total_chunks, status}` |
| `POST` | `/api/uploads/<id>/complete` | — | `FileRecord` |
| `POST` | `/api/uploads/<id>/abort` | — | `{ok, status:"aborted"}` |
| `GET`  | `/api/files` | — | `FileRecord[]` |
| `GET`  | `/api/files/<id>` | — | `FileRecord` |
| `GET`  | `/api/files/<id>/download` | — | binary stream |
| `GET`  | `/metrics`, `/health` | — | metrics / health |

---

## 5. Data model

### Upload

```json
{
  "upload_id": 42,
  "filename": "report.pdf",
  "content_type": "application/pdf",
  "size": 4194304,
  "chunk_size": 262144,
  "user_id": "u-123",
  "status": "in_progress",
  "received": [0, 1, 2, 4, 5],
  "sha256": null,
  "file_id": null
}
```

### FileRecord (post-completion)

```json
{
  "file_id": "ab12cd34...",
  "filename": "report.pdf",
  "content_type": "application/pdf",
  "size": 4194304,
  "upload_id": 42,
  "user_id": "u-123",
  "path": "var/files/ab12cd34...",
  "sha256": "..."
}
```

### On-disk layout

```
var/
  uploads/<upload_id>/<idx:08d>     # one file per chunk
  files/<file_id>                    # final stitched file
```

---

## 6. Write path deep dive

**Init**: validate inputs, assign `upload_id`, persist `upload:<id>`,
create the chunk directory.

**Chunk PUT**: write the chunk to `uploads/<id>/<idx>`, append `idx` to
`upload:<id>.received`, and flip status to `in_progress`. The check
against `chunk_size` rejects an oversized chunk, but allows the last
chunk to be smaller.

**Complete**:
1. Compute the expected number of chunks and verify none are missing.
2. Walk the chunks in order, hashing and writing to `files/<file_id>`.
3. Compare final size to declared size; reject on mismatch.
4. Persist the `file:<file_id>` record and the back-reference
   `file_by_upload:<upload_id> = file_id`.
5. Delete the chunk directory.

**Abort**: mark `status=aborted` and delete the chunk directory.
Subsequent `put_chunk` calls return 400.

---

## 7. Read path deep dive

`GET /api/uploads/<id>/status` computes `total_chunks =
ceil(size / chunk_size)` and returns `received` + `missing`. The
client uses this to resume: it uploads only `missing`.

`GET /api/files/<id>/download` reads the final file from disk and
streams it back. In production the same API would issue a 302 to a
pre-signed S3 URL.

---

## 8. Failure modes

| Failure | Mitigation |
|---|---|
| Network drop mid-chunk | Re-issue on retry; chunk write is idempotent. |
| Client crashes | `/status` tells the client what's still missing. |
| Wrong chunk size | Server clamps; oversized chunk returns 400. |
| Disk full on /complete | Partial file unlinked; upload remains `in_progress`. |
| File tampering | SHA-256 over chunks; mismatch on `/complete` rejected. |
| Path traversal in filename | Reject any filename containing `/` or `\`. |

---

## 9. Tradeoffs

- **Local FS vs object storage**: the local FS is great for course
  clarity. In production, each chunk is a `PUT` to S3 with
  `partNumber=<idx>` and `/complete` is S3's `CompleteMultipartUpload`.
- **Whole-file re-hash vs streaming hash**: we hash while concatenating,
  so we never hold 2 GB in memory.
- **Status endpoint per upload vs push**: clients poll `/status`. A
  real chat app could push status via WebSocket; the data model is
  identical.
- **Single replica vs replicated**: in production, chunk state goes in
  a shared store (S3, GCS) so any app replica can answer `/status`.

---

## 10. Code map

| File | Role |
|---|---|
| `code/service.py` | `FileUploader` — initiate, put chunk, status, complete, abort, download. |
| `code/app.py` | Flask HTTP service with raw-binary PUT for chunks. |
| `tests/test_service.py` | Service-level tests (validation, resume, complete, abort, integrity). |
| `tests/test_app.py` | HTTP-level tests covering the full upload flow + status + metrics. |
