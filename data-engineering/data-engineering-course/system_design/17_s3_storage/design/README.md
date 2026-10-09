# 17 — S3-style Distributed Object Storage

> **Lesson 17 of the Distributed Data Storage & Partitioning track**

A from-scratch object store with buckets, keys, multipart upload hints,
ETag (md5), prefix listing, and version tracking — the smallest surface
that captures the actual S3 API contract. Binary content lives in
`var/<bucket>/<key>` blobs; metadata lives in a `KeyValueStore`.

---

## 1. Requirements

### Functional
- `PUT /<bucket>/<key>` (body) — write object.
- `GET /<bucket>/<key>` — read object body.
- `HEAD /<bucket>/<key>` — return metadata only.
- `GET /<bucket>/?prefix=foo` — list keys with prefix.
- `DELETE /<bucket>/<key>` — remove object (creates a delete marker if versioning).
- `POST /<bucket>/<key>?uploadId=...&partNumber=N` — multipart upload.
- `POST /<bucket>/<key>?uploadId=...&complete` — complete multipart.
- Version tracking — each PUT produces a new version_id.

### Non-functional
- **Durability** — atomic write via tmp + rename.
- **ETag** — md5 of body for change detection.
- **Pagination** — list returns up to N items; callers drive continuations.
- **Same key as bucket/blob** boundaries — no path traversal.

### Out of scope
- Real presigned URLs, IAM.
- Multipart by-part replication.
- Compaction / garbage collection of old versions.

---

## 2. Capacity estimation

| Metric | Value |
|---|---|
| Buckets per account | 1k |
| Objects per bucket | unlimited |
| Object size | 0 B – 5 TB |
| Multipart parts | up to 10,000 |
| ETag | md5 hex (32 chars) |

---

## 3. High-level design

```
   client ──► [ Flask router ]
                    │
        path:  /<bucket>/<key>[?uploadId=...&partNumber=N]
                    │
                    ▼
   [ ObjectStoreService ]
        │
   ┌────┴─────────────┬───────────────────┐
   │                  │                   │
   ▼                  ▼                   ▼
buckets.json     var/<bucket>/<key>    parts/<upload_id>/<part>/
(KeyValueStore)  (binary blob)          (binary parts)
```

- Path-based dispatch: Flask view function reads bucket/key from URL.
- Metadata in `KeyValueStore`: bucket list, object index, version chain.
- Blobs in `var/<bucket>/<key>`; temp file + atomic rename for durability.

---

## 4. API

| Method | Path | Body / Params | Returns |
|---|---|---|---|
| `PUT`    | `/<bucket>/<key>` | raw body | `{key, etag, size, version_id}` |
| `GET`    | `/<bucket>/<key>` | optional `?versionId=...` | binary body (with metadata headers) |
| `HEAD`   | `/<bucket>/<key>` | — | headers: content-length, etag, x-version-id |
| `DELETE` | `/<bucket>/<key>` | — | `{deleted: true, version_id}` |
| `GET`    | `/<bucket>/` | `?prefix=...&max_keys=N` | `{name, prefix, keys, is_truncated}` |
| `POST`   | `/<bucket>/<key>?uploadId=...&partNumber=N` | raw body | `{part_number, etag, size}` |
| `POST`   | `/<bucket>/<key>?uploadId=...&complete` | (no body, parts in service) | `{key, etag, size, version_id}` |
| `GET`    | `/metrics` | — | counters |
| `GET`    | `/health` | — | `{"ok": true}` |

Buckets auto-create on first PUT (S3-like).

---

## 5. Data model

### Buckets
```
bucket:<name> = {"name": str, "created_at": float}
```

### Object index
```
obj:<bucket>/<key> = {
  "current_version": str,
  "versions": {
    "v0": {"etag": str, "size": int, "mtime": float, "deleted": bool},
    ...
  }
}
```

### Multipart
```
mp:<upload_id> = {
  "bucket": str,
  "key": str,
  "parts": {part_number: {"etag": str, "size": int, "path": str}},
  "created_at": float,
}
```

### Blob
`var/<bucket>/<key>` (current) — atomic write via tmp + rename. Old versions
under `var/<bucket>/<key>@v0`, `var/<bucket>/<key>@v1`, etc.

---

## 6. Read path

`GET /<bucket>/<key>`:
1. Look up `obj:<bucket>/<key>`. Resolve `?versionId=` or current.
2. Open blob, stream to client.
3. Set `ETag`, `Content-Length`, `x-version-id` headers.

`HEAD /<bucket>/<key>`: same path, no body.

`GET /<bucket>/?prefix=...`: scan `KeyValueStore` for `obj:<bucket>/<key>`,
filter by prefix, paginate.

---

## 7. Write path

`PUT /<bucket>/<key>`:
1. Ensure bucket exists.
2. Compute md5 of body → ETag.
3. Write to `var/<bucket>/<key>.<uuid>.tmp` then atomic rename.
4. Bump version. Update index.
5. Return `{key, etag, size, version_id}`.

`DELETE`: append a tombstone version with `deleted=true`.

Multipart:
- `POST ?uploadId=...&partNumber=N` writes part to `var/mp/<upload_id>/<N>`.
- `POST ?uploadId=...&complete` concatenates parts in order, writes final blob.

---

## 8. Failure modes

| Failure | Mitigation |
|---|---|
| Partial write | Atomic rename; tmp scrubbed. |
| Concurrent PUTs | Last-writer-wins (versioned). |
| Listing large bucket | Prefix scan + pagination. |
| Multipart parts leakage | GC: complete or abort after TTL. Out of scope. |
| Bad path | Reject slashes / `..` in key. |

---

## 9. Tradeoffs

- **Filesystem vs object store**: FS is fast for a course demo. In prod,
  you'd use S3 itself (or GCS / Azure Blob). The design maps cleanly.
- **Versioning storage cost**: keep N versions grows linearly. We expose
  the version list but don't GC — that's a separate compaction process.
- **ETag = md5**: matches S3 for non-multipart. Multipart uses `-N` style.
- **Auth / ACLs**: out of scope; buckets are open in this demo.

---

## 10. How the code maps to this design

| File | Role |
|---|---|
| `code/service.py` | `ObjectStoreService` + multipart upload. |
| `code/app.py` | Flask HTTP service with path-based dispatch. |
| `tests/test_service.py` | PUT/GET/HEAD, versions, multipart, prefix listing. |
| `tests/test_app.py` | HTTP-level tests using Flask test client. |
