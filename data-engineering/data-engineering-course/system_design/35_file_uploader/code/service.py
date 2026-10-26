"""Chunked File Uploader — core service.

A resumable, chunked file-upload service for AI chat apps. The
engineering problem is the same as S3 multipart uploads / tus.io:

    1. Client calls /initiate to get a `chunk_size` and `upload_id`.
    2. Client uploads each chunk with PUT /chunks/<idx>.
    3. The server can answer GET /status at any time so the client
       knows which chunks it still needs to send (resume).
    4. Client calls /complete; the server stitches chunks into a
       single file and assigns a `file_id`.
    5. Anyone with the `file_id` can call /files/<id>/download to
       retrieve the original file.

The state machine for an upload:

    initiated ──(any chunks)──► in_progress ──(complete)──► completed
         │                            │
         └──────(abort)──────► aborted ┘

Storage: each chunk is a file under `var/uploads/<upload_id>/<idx>`;
on completion we concatenate to `var/files/<file_id>` and remove the
chunk directory.
"""

from __future__ import annotations

import hashlib
import os
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

from common.storage import KeyValueStore


# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------


DEFAULT_CHUNK_SIZE = 256 * 1024  # 256 KB
MIN_CHUNK_SIZE = 64 * 1024
MAX_CHUNK_SIZE = 16 * 1024 * 1024
MAX_FILE_SIZE = 2 * 1024 * 1024 * 1024  # 2 GB
MAX_FILENAME = 255

ALLOWED_CONTENT_TYPES_PREFIX = (
    "text/",
    "application/json",
    "application/pdf",
    "application/octet-stream",
    "image/",
    "audio/",
    "video/",
)


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class Upload:
    upload_id: int
    filename: str
    content_type: str
    size: int
    chunk_size: int
    user_id: str
    status: str  # "initiated" | "in_progress" | "completed" | "aborted"
    created_at: float = field(default_factory=lambda: time.time())
    completed_at: Optional[float] = None
    file_id: Optional[str] = None
    received: list[int] = field(default_factory=list)  # chunk indices
    sha256: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class FileRecord:
    file_id: str
    filename: str
    content_type: str
    size: int
    upload_id: int
    user_id: str
    created_at: float = field(default_factory=lambda: time.time())
    path: str = ""
    sha256: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class FileUploader:
    """A chunked, resumable uploader.

    >>> import tempfile
    >>> root = tempfile.mkdtemp()
    >>> svc = FileUploader(root=root)
    >>> up = svc.initiate("a.txt", 6, "text/plain", user_id="u1")
    >>> svc.put_chunk(up.upload_id, 0, b"hello ")
    True
    >>> svc.put_chunk(up.upload_id, 1, b"world!")
    True
    >>> rec = svc.complete(up.upload_id)
    >>> rec.size
    12
    >>> svc.download(rec.file_id)
    b'hello world!'
    """

    def __init__(
        self,
        store: Optional[KeyValueStore] = None,
        root: Optional[str | Path] = None,
        default_chunk_size: int = DEFAULT_CHUNK_SIZE,
    ):
        self.store = store or KeyValueStore("file_uploader")
        self.root = Path(root or "var")
        (self.root / "uploads").mkdir(parents=True, exist_ok=True)
        (self.root / "files").mkdir(parents=True, exist_ok=True)
        self.default_chunk_size = default_chunk_size
        self._next_upload_id = self._max_upload_id() + 1

    def _max_upload_id(self) -> int:
        best = 0
        for k, _ in self.store.scan("upload:"):
            try:
                best = max(best, int(k.split(":")[1]))
            except (IndexError, ValueError):
                continue
        return best

    # ---- validation ----------------------------------------------------

    @staticmethod
    def _validate_filename(name: str) -> None:
        if not isinstance(name, str) or not name:
            raise ValueError("filename is required")
        if len(name) > MAX_FILENAME:
            raise ValueError(f"filename too long (>{MAX_FILENAME})")
        if "/" in name or "\\" in name or name in (".", ".."):
            raise ValueError("filename must not contain path separators")

    @staticmethod
    def _validate_content_type(ct: str) -> None:
        if not isinstance(ct, str) or not ct:
            raise ValueError("content_type is required")
        if not any(ct.startswith(p) for p in ALLOWED_CONTENT_TYPES_PREFIX):
            raise ValueError(f"content_type '{ct}' not allowed")

    @staticmethod
    def _validate_size(size: int) -> None:
        if not isinstance(size, int) or size <= 0:
            raise ValueError("size must be a positive integer")
        if size > MAX_FILE_SIZE:
            raise ValueError(f"size > {MAX_FILE_SIZE} bytes not allowed")

    @staticmethod
    def _validate_chunk_size(chunk_size: int) -> int:
        if not isinstance(chunk_size, int) or chunk_size <= 0:
            raise ValueError("chunk_size must be a positive integer")
        if chunk_size < MIN_CHUNK_SIZE:
            return MIN_CHUNK_SIZE
        if chunk_size > MAX_CHUNK_SIZE:
            return MAX_CHUNK_SIZE
        return chunk_size

    # ---- initiate ------------------------------------------------------

    def initiate(
        self,
        filename: str,
        size: int,
        content_type: str = "application/octet-stream",
        user_id: str = "anonymous",
        chunk_size: Optional[int] = None,
    ) -> Upload:
        self._validate_filename(filename)
        self._validate_size(size)
        self._validate_content_type(content_type)
        cs = self._validate_chunk_size(chunk_size or self.default_chunk_size)

        up_id = self._next_upload_id
        self._next_upload_id += 1
        up = Upload(
            upload_id=up_id,
            filename=filename,
            content_type=content_type,
            size=size,
            chunk_size=cs,
            user_id=user_id,
            status="initiated",
        )
        (self.root / "uploads" / str(up_id)).mkdir(parents=True, exist_ok=True)
        self._persist(up)
        return up

    # ---- chunks --------------------------------------------------------

    def get_upload(self, upload_id: int) -> Optional[Upload]:
        d = self.store.get(f"upload:{upload_id}")
        if not d:
            return None
        return Upload(**d)

    def put_chunk(self, upload_id: int, idx: int, data: bytes) -> bool:
        up = self.get_upload(upload_id)
        if not up:
            raise ValueError("upload not found")
        if up.status in ("completed", "aborted"):
            raise ValueError(f"upload is {up.status}")
        if not isinstance(idx, int) or idx < 0:
            raise ValueError("idx must be a non-negative integer")
        if not isinstance(data, (bytes, bytearray)):
            raise ValueError("data must be bytes")

        chunk_path = self.root / "uploads" / str(upload_id) / f"{idx:08d}"
        # Refuse a chunk larger than the agreed chunk_size, except the
        # last one which can be smaller.
        if len(data) > up.chunk_size:
            raise ValueError(
                f"chunk {idx} too large ({len(data)} > {up.chunk_size})"
            )
        chunk_path.write_bytes(bytes(data))
        if idx not in up.received:
            up.received.append(idx)
            up.received.sort()
        if up.status == "initiated":
            up.status = "in_progress"
        self._persist(up)
        return True

    def missing_chunks(self, upload_id: int) -> list[int]:
        up = self.get_upload(upload_id)
        if not up:
            return []
        total = (up.size + up.chunk_size - 1) // up.chunk_size
        return [i for i in range(total) if i not in up.received]

    def status(self, upload_id: int) -> Optional[dict]:
        up = self.get_upload(upload_id)
        if not up:
            return None
        total = (up.size + up.chunk_size - 1) // up.chunk_size
        return {
            "upload_id": up.upload_id,
            "filename": up.filename,
            "size": up.size,
            "chunk_size": up.chunk_size,
            "total_chunks": total,
            "received": len(up.received),
            "missing": self.missing_chunks(upload_id),
            "status": up.status,
            "file_id": up.file_id,
        }

    # ---- abort / complete ----------------------------------------------

    def abort(self, upload_id: int) -> bool:
        up = self.get_upload(upload_id)
        if not up:
            return False
        up.status = "aborted"
        self._persist(up)
        self._rm_tree(self.root / "uploads" / str(upload_id))
        return True

    def complete(self, upload_id: int) -> FileRecord:
        up = self.get_upload(upload_id)
        if not up:
            raise ValueError("upload not found")
        if up.status == "completed":
            # Idempotent — return the existing file record.
            return self._load_file_by_upload(upload_id)
        if up.status == "aborted":
            raise ValueError("upload was aborted")
        missing = self.missing_chunks(upload_id)
        if missing:
            raise ValueError(f"missing chunks: {missing[:10]}"
                             + ("..." if len(missing) > 10 else ""))

        # Concatenate in order, computing a sha256 along the way.
        h = hashlib.sha256()
        total = (up.size + up.chunk_size - 1) // up.chunk_size
        # Allocate a final file id.
        file_id = hashlib.sha256(
            f"{up.upload_id}:{up.filename}:{time.time_ns()}".encode()
        ).hexdigest()[:24]
        out_path = self.root / "files" / file_id
        with open(out_path, "wb") as out:
            for i in range(total):
                p = self.root / "uploads" / str(upload_id) / f"{i:08d}"
                chunk = p.read_bytes()
                out.write(chunk)
                h.update(chunk)
        # Validate final size.
        actual = out_path.stat().st_size
        if actual != up.size:
            out_path.unlink(missing_ok=True)
            raise ValueError(
                f"size mismatch: declared {up.size}, got {actual}"
            )

        rec = FileRecord(
            file_id=file_id,
            filename=up.filename,
            content_type=up.content_type,
            size=actual,
            upload_id=up.upload_id,
            user_id=up.user_id,
            path=str(out_path),
            sha256=h.hexdigest(),
        )
        up.status = "completed"
        up.completed_at = rec.created_at
        up.file_id = file_id
        up.sha256 = rec.sha256
        self._persist(up)
        self.store.set(f"file:{file_id}", rec.to_dict())
        self.store.set(f"file_by_upload:{up.upload_id}", file_id)
        # Free the chunk directory.
        self._rm_tree(self.root / "uploads" / str(upload_id))
        return rec

    def download(self, file_id: str) -> bytes:
        rec = self.get_file(file_id)
        if not rec:
            raise ValueError("file not found")
        return Path(rec.path).read_bytes()

    def get_file(self, file_id: str) -> Optional[FileRecord]:
        d = self.store.get(f"file:{file_id}")
        if not d:
            return None
        return FileRecord(**d)

    def list_files(self, user_id: Optional[str] = None) -> list[FileRecord]:
        out: list[FileRecord] = []
        for k, _ in self.store.scan("file:"):
            d = self.store.get(k)
            if d and (user_id is None or d.get("user_id") == user_id):
                out.append(FileRecord(**d))
        out.sort(key=lambda f: f.created_at, reverse=True)
        return out

    # ---- internals -----------------------------------------------------

    def _load_file_by_upload(self, upload_id: int) -> FileRecord:
        file_id = self.store.get(f"file_by_upload:{upload_id}")
        if not file_id:
            raise ValueError("upload is completed but file record missing")
        rec = self.get_file(file_id)
        if not rec:
            raise ValueError("file record missing")
        return rec

    def _persist(self, up: Upload) -> None:
        self.store.set(f"upload:{up.upload_id}", up.to_dict())

    @staticmethod
    def _rm_tree(p: Path) -> None:
        if not p.exists():
            return
        for child in p.iterdir():
            if child.is_file():
                child.unlink()
            else:
                FileUploader._rm_tree(child)
        p.rmdir()
