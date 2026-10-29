"""Dropbox-style file sync — core service.

Implements:
  * FixedSizeChunker / RabinKarpChunker  — split content into chunks.
  * ChunkStore  — dedup storage, content-addressed by SHA-256.
  * FileSyncService  — high-level upload / download / list.
"""

from __future__ import annotations

import base64
import hashlib
import os
import threading
import time
from dataclasses import dataclass, field
from typing import Iterable, Optional, Protocol

from common.storage import KeyValueStore
from common.ids import Snowflake

DEFAULT_CHUNK_SIZE = 4 * 1024 * 1024  # 4 MB
MIN_CDC = 1 * 1024 * 1024  # 1 MB
MAX_CDC = 8 * 1024 * 1024  # 8 MB
CDC_MASK = (1 << 13) - 1  # average chunk ~ 8 KB at 13 bits — too small for the
# course. We use a larger window to keep chunk counts reasonable.


# ---------------------------------------------------------------------------
# Chunkers
# ---------------------------------------------------------------------------


class Chunker(Protocol):
    def chunks(self, data: bytes) -> Iterable[tuple[int, int]]:
        """Yield (offset, length) tuples covering ``data``."""
        ...


class FixedSizeChunker:
    """Slice data into fixed-size windows."""

    def __init__(self, size: int = DEFAULT_CHUNK_SIZE):
        self.size = max(1, size)

    def chunks(self, data: bytes) -> Iterable[tuple[int, int]]:
        n = len(data)
        for off in range(0, n, self.size):
            yield off, min(self.size, n - off)


class RabinKarpChunker:
    """Content-defined chunker using a Rabin-Karp rolling hash.

    Splits on a 13-bit mask so chunks average ~8 KB. We relax the bounds to
    ``min_size``/``max_size`` to keep chunk counts small for course demos.
    """

    def __init__(
        self,
        min_size: int = MIN_CDC,
        max_size: int = MAX_CDC,
        mask: int = CDC_MASK,
    ):
        self.min_size = min_size
        self.max_size = max_size
        self.mask = mask

    def chunks(self, data: bytes) -> Iterable[tuple[int, int]]:
        n = len(data)
        if n == 0:
            return
        start = 0
        end = self.min_size
        rh = 0
        # Pre-compute base. We use 257 — a small prime works for byte hashing.
        base = 257
        # Hash a 4-byte rolling window.
        W = 4
        if n <= self.min_size:
            yield 0, n
            return
        # Build initial hash from the first `min_size` window end-region.
        for i in range(end - W, end):
            rh = (rh * base + data[i]) & 0xFFFFFFFFFFFFFFFF
        while end < n:
            if (rh & self.mask) == 0 and end - start >= self.min_size:
                yield start, end - start
                start = end
                end = min(end + self.min_size, n)
                rh = 0
                if end - W >= start:
                    for i in range(end - W, end):
                        rh = (rh * base + data[i]) & 0xFFFFFFFFFFFFFFFF
                continue
            # Slide window
            rh = (rh * base + data[end]) & 0xFFFFFFFFFFFFFFFF
            # Subtract the byte leaving the window (after enough history).
            if end - W >= start:
                out = data[end - W]
                rh = (rh - out * pow(base, W, (1 << 64))) & 0xFFFFFFFFFFFFFFFF
            end += 1
            if end - start >= self.max_size:
                yield start, end - start
                start = end
                rh = 0
                if end + W <= n:
                    for i in range(end, min(end + W, n)):
                        rh = (rh * base + data[i]) & 0xFFFFFFFFFFFFFFFF
                    end += W
        if start < n:
            yield start, n - start


# ---------------------------------------------------------------------------
# Chunk store (content-addressed, deduped)
# ---------------------------------------------------------------------------


class ChunkStore:
    """Content-addressed chunk storage.

    Backing: ``var/chunks/<hash>`` on disk + a `KeyValueStore` index for
    refcount and size.
    """

    def __init__(self, base_dir: str, kv: Optional[KeyValueStore] = None):
        self.base_dir = base_dir
        self.kv = kv or KeyValueStore(
            "chunks", persist_path=os.path.join(base_dir, "_chunks.json")
        )
        os.makedirs(self._chunk_path("00"), exist_ok=True)
        self._lock = threading.RLock()

    def _chunk_path(self, h: str) -> str:
        # Two-level dir tree to keep directories small.
        return os.path.join(self.base_dir, h[:2], h)

    def _index_key(self, h: str) -> str:
        return f"chunk:{h}"

    def has(self, h: str) -> bool:
        return os.path.exists(self._chunk_path(h))

    def get(self, h: str) -> Optional[bytes]:
        path = self._chunk_path(h)
        if not os.path.exists(path):
            return None
        with open(path, "rb") as f:
            return f.read()

    def put(self, data: bytes) -> str:
        h = hashlib.sha256(data).hexdigest()
        with self._lock:
            path = self._chunk_path(h)
            if os.path.exists(path):
                # Bump refcount
                rec = self.kv.get(self._index_key(h), {"size": len(data), "refcount": 0})
                rec["refcount"] = rec.get("refcount", 0) + 1
                self.kv.set(self._index_key(h), rec)
                return h
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "wb") as f:
                f.write(data)
            self.kv.set(self._index_key(h), {"size": len(data), "refcount": 1})
            return h

    def refcount(self, h: str) -> int:
        rec = self.kv.get(self._index_key(h), {"size": 0, "refcount": 0})
        return rec.get("refcount", 0)

    def stats(self) -> dict:
        with self._lock:
            total = 0
            refs = 0
            for k, v in self.kv.all().items():
                if k.startswith("chunk:"):
                    total += 1
                    refs += v.get("refcount", 0)
            return {
                "unique_chunks": total,
                "refcount_total": refs,
            }


# ---------------------------------------------------------------------------
# File sync service
# ---------------------------------------------------------------------------


@dataclass
class FileRecord:
    id: str
    filename: str
    size: int
    chunk_size: int
    chunks: list[dict]  # [{"hash": str, "size": int}, ...]
    version: int = 1
    mtime: float = field(default_factory=time.time)
    uploaded_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "filename": self.filename,
            "size": self.size,
            "chunk_size": self.chunk_size,
            "chunks": list(self.chunks),
            "version": self.version,
            "mtime": self.mtime,
            "uploaded_at": self.uploaded_at,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "FileRecord":
        return cls(
            id=d["id"],
            filename=d["filename"],
            size=d["size"],
            chunk_size=d.get("chunk_size", DEFAULT_CHUNK_SIZE),
            chunks=list(d.get("chunks", [])),
            version=d.get("version", 1),
            mtime=d.get("mtime", 0.0),
            uploaded_at=d.get("uploaded_at", 0.0),
        )


class FileSyncService:
    """Dropbox-like sync. Chunk + dedup + versioned metadata."""

    def __init__(
        self,
        base_dir: str,
        chunker: Optional[Chunker] = None,
        snowflake: Optional[Snowflake] = None,
    ):
        self.base_dir = base_dir
        self.chunker = chunker or FixedSizeChunker(DEFAULT_CHUNK_SIZE)
        os.makedirs(base_dir, exist_ok=True)
        self.chunk_store = ChunkStore(os.path.join(base_dir, "chunks"))
        self._files = KeyValueStore(
            "files", persist_path=os.path.join(base_dir, "files.json")
        )
        self._lock = threading.RLock()
        self.snow = snowflake or Snowflake(machine_id=1)

    # ---- write ---------------------------------------------------------

    def upload(self, filename: str, content: bytes) -> FileRecord:
        with self._lock:
            chunks: list[dict] = []
            for off, length in self.chunker.chunks(content):
                piece = content[off:off + length]
                h = self.chunk_store.put(piece)
                chunks.append({"hash": h, "size": len(piece)})
            # Versioning: if filename exists, bump version
            existing = self._files.get(f"name:{filename}")
            version = 1
            old_id = None
            if existing:
                version = existing.get("version", 1) + 1
                old_id = existing.get("id")
            new_id = str(self.snow.next_id())
            rec = FileRecord(
                id=new_id,
                filename=filename,
                size=len(content),
                chunk_size=getattr(self.chunker, "size", DEFAULT_CHUNK_SIZE),
                chunks=chunks,
                version=version,
                mtime=time.time(),
            )
            self._files.set(f"file:{new_id}", rec.to_dict())
            self._files.set(f"name:{filename}", {"id": new_id, "version": version})
            if old_id:
                # Don't drop old chunks — refcounting tracks them.
                pass
            return rec

    # ---- read ----------------------------------------------------------

    def get_file(self, file_id: str) -> Optional[FileRecord]:
        d = self._files.get(f"file:{file_id}")
        if not d:
            return None
        return FileRecord.from_dict(d)

    def get_by_name(self, filename: str) -> Optional[FileRecord]:
        meta = self._files.get(f"name:{filename}")
        if not meta:
            return None
        return self.get_file(meta["id"])

    def download(self, file_id: str) -> Optional[tuple[str, bytes]]:
        rec = self.get_file(file_id)
        if rec is None:
            return None
        parts: list[bytes] = []
        for c in rec.chunks:
            data = self.chunk_store.get(c["hash"])
            if data is None:
                return None
            parts.append(data)
        return rec.filename, b"".join(parts)

    def list_files(self) -> list[dict]:
        out: list[dict] = []
        for k, v in self._files.all().items():
            if k.startswith("file:"):
                out.append(v)
        return out

    def get_chunk(self, h: str) -> Optional[bytes]:
        return self.chunk_store.get(h)

    def stats(self) -> dict:
        return {
            "files": sum(1 for k in self._files.all() if k.startswith("file:")),
            "chunks": self.chunk_store.stats(),
        }

    # ---- utilities -----------------------------------------------------

    @staticmethod
    def encode_b64(b: bytes) -> str:
        return base64.b64encode(b).decode("ascii")

    @staticmethod
    def decode_b64(s: str) -> bytes:
        return base64.b64decode(s.encode("ascii"))
