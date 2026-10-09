"""S3-style Object Store — core service.

Implements:
  * Bucket auto-creation.
  * Object PUT/GET/HEAD/DELETE with versioning.
  * ETag = md5(body) for single-shot, md5(concat) for multipart.
  * Multipart upload: init / part / complete.
  * Prefix listing with pagination.
"""

from __future__ import annotations

import hashlib
import os
import re
import time
import uuid
from dataclasses import dataclass, field
from typing import Optional

from common.storage import KeyValueStore

SAFE_KEY_RE = re.compile(r"^[A-Za-z0-9._\-/]+$")


def _is_safe_key(key: str) -> bool:
    if not key or ".." in key.split("/"):
        return False
    return bool(SAFE_KEY_RE.match(key))


def _md5(data: bytes) -> str:
    return hashlib.md5(data).hexdigest()


@dataclass
class ObjectVersion:
    version_id: str
    etag: str
    size: int
    mtime: float
    deleted: bool = False
    blob_path: str = ""

    def to_dict(self) -> dict:
        return {
            "version_id": self.version_id,
            "etag": self.etag,
            "size": self.size,
            "mtime": self.mtime,
            "deleted": self.deleted,
            "blob_path": self.blob_path,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ObjectVersion":
        return cls(
            version_id=d["version_id"],
            etag=d["etag"],
            size=d.get("size", 0),
            mtime=d.get("mtime", 0.0),
            deleted=d.get("deleted", False),
            blob_path=d.get("blob_path", ""),
        )


@dataclass
class ObjectRecord:
    bucket: str
    key: str
    current_version: str
    versions: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "bucket": self.bucket,
            "key": self.key,
            "current_version": self.current_version,
            "versions": {k: v.to_dict() for k, v in self.versions.items()},
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ObjectRecord":
        return cls(
            bucket=d["bucket"],
            key=d["key"],
            current_version=d["current_version"],
            versions={k: ObjectVersion.from_dict(v) for k, v in d.get("versions", {}).items()},
        )


@dataclass
class MultipartPart:
    part_number: int
    etag: str
    size: int
    path: str

    def to_dict(self) -> dict:
        return {
            "part_number": self.part_number,
            "etag": self.etag,
            "size": self.size,
            "path": self.path,
        }


@dataclass
class MultipartUpload:
    upload_id: str
    bucket: str
    key: str
    parts: dict = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "upload_id": self.upload_id,
            "bucket": self.bucket,
            "key": self.key,
            "parts": {k: v.to_dict() for k, v in self.parts.items()},
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "MultipartUpload":
        parts = {int(k): MultipartPart(**v) for k, v in d.get("parts", {}).items()}
        return cls(
            upload_id=d["upload_id"],
            bucket=d["bucket"],
            key=d["key"],
            parts=parts,
            created_at=d.get("created_at", 0.0),
        )


class ObjectStoreService:
    """S3-like object storage with versioning + multipart."""

    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        os.makedirs(base_dir, exist_ok=True)
        self.kv = KeyValueStore(
            "objects", persist_path=os.path.join(base_dir, "objects.json")
        )

    # ---- bucket helpers ------------------------------------------------

    def _bucket_path(self, bucket: str) -> str:
        path = os.path.join(self.base_dir, bucket)
        os.makedirs(path, exist_ok=True)
        return path

    def ensure_bucket(self, bucket: str) -> None:
        if not re.match(r"^[a-z0-9][a-z0-9.\-]{1,61}[a-z0-9]$", bucket):
            raise ValueError(f"invalid bucket name {bucket!r}")
        self._bucket_path(bucket)
        self.kv.set(f"bucket:{bucket}", {"name": bucket, "created_at": time.time()})

    def list_buckets(self) -> list[str]:
        return sorted(
            k.split(":", 1)[1]
            for k in self.kv.all().keys()
            if k.startswith("bucket:")
        )

    # ---- object index ---------------------------------------------------

    def _obj_key(self, bucket: str, key: str) -> str:
        return f"obj:{bucket}:{key}"

    def _load_object(self, bucket: str, key: str) -> Optional[ObjectRecord]:
        d = self.kv.get(self._obj_key(bucket, key))
        if not d:
            return None
        return ObjectRecord.from_dict(d)

    def _save_object(self, rec: ObjectRecord) -> None:
        self.kv.set(self._obj_key(rec.bucket, rec.key), rec.to_dict())

    # ---- atomic write ---------------------------------------------------

    def _atomic_write(self, path: str, data: bytes) -> None:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        tmp = f"{path}.{uuid.uuid4().hex}.tmp"
        with open(tmp, "wb") as f:
            f.write(data)
        os.replace(tmp, path)

    # ---- PUT / GET / HEAD / DELETE -------------------------------------

    def put(self, bucket: str, key: str, data: bytes) -> dict:
        if not _is_safe_key(key):
            raise ValueError(f"invalid key {key!r}")
        self.ensure_bucket(bucket)
        version_id = uuid.uuid4().hex
        # Version-specific blob path so old versions survive.
        blob_path = os.path.join(self._bucket_path(bucket), f"{key}@{version_id}")
        self._atomic_write(blob_path, data)
        rec = self._load_object(bucket, key) or ObjectRecord(
            bucket=bucket, key=key, current_version=version_id,
        )
        rec.versions[version_id] = ObjectVersion(
            version_id=version_id,
            etag=_md5(data),
            size=len(data),
            mtime=time.time(),
            blob_path=blob_path,
        )
        rec.current_version = version_id
        self._save_object(rec)
        return {
            "bucket": bucket,
            "key": key,
            "version_id": version_id,
            "etag": rec.versions[version_id].etag,
            "size": len(data),
            "mtime": rec.versions[version_id].mtime,
        }

    def get(self, bucket: str, key: str, version_id: Optional[str] = None) -> Optional[tuple[bytes, ObjectVersion]]:
        rec = self._load_object(bucket, key)
        if rec is None:
            return None
        if version_id is None:
            version_id = rec.current_version
        if version_id not in rec.versions:
            return None
        v = rec.versions[version_id]
        if v.deleted:
            return None
        if not v.blob_path or not os.path.exists(v.blob_path):
            return None
        with open(v.blob_path, "rb") as f:
            return f.read(), v

    def head(self, bucket: str, key: str, version_id: Optional[str] = None) -> Optional[ObjectVersion]:
        rec = self._load_object(bucket, key)
        if rec is None:
            return None
        if version_id is None:
            version_id = rec.current_version
        if version_id not in rec.versions:
            return None
        return rec.versions[version_id]

    def delete(self, bucket: str, key: str) -> Optional[str]:
        rec = self._load_object(bucket, key)
        if rec is None:
            return None
        version_id = uuid.uuid4().hex
        rec.versions[version_id] = ObjectVersion(
            version_id=version_id,
            etag=rec.versions[rec.current_version].etag,
            size=0,
            mtime=time.time(),
            deleted=True,
            blob_path="",
        )
        rec.current_version = version_id
        self._save_object(rec)
        return version_id

    # ---- listing -------------------------------------------------------

    def list_objects(self, bucket: str, prefix: str = "", max_keys: int = 1000) -> list[dict]:
        if bucket not in self.list_buckets():
            return []
        prefix_obj = f"obj:{bucket}:{prefix}"
        out: list[dict] = []
        for k, v in self.kv.all().items():
            if not k.startswith(prefix_obj):
                continue
            obj = ObjectRecord.from_dict(v)
            cv = obj.versions.get(obj.current_version)
            if cv is None or cv.deleted:
                continue
            out.append({
                "key": obj.key,
                "size": cv.size,
                "etag": cv.etag,
                "version_id": obj.current_version,
                "mtime": cv.mtime,
            })
            if len(out) >= max_keys:
                break
        return out

    # ---- multipart ----------------------------------------------------

    def init_multipart(self, bucket: str, key: str) -> str:
        if not _is_safe_key(key):
            raise ValueError(f"invalid key {key!r}")
        self.ensure_bucket(bucket)
        upload_id = uuid.uuid4().hex
        mp = MultipartUpload(upload_id=upload_id, bucket=bucket, key=key)
        self.kv.set(f"mp:{upload_id}", mp.to_dict())
        # Stash empty parts dir.
        os.makedirs(os.path.join(self.base_dir, "mp", upload_id), exist_ok=True)
        return upload_id

    def upload_part(self, upload_id: str, part_number: int, data: bytes) -> dict:
        if part_number < 1 or part_number > 10_000:
            raise ValueError("part_number must be in [1, 10000]")
        d = self.kv.get(f"mp:{upload_id}")
        if not d:
            raise ValueError(f"unknown upload_id {upload_id}")
        mp = MultipartUpload.from_dict(d)
        part_path = os.path.join(self.base_dir, "mp", upload_id, f"part_{part_number}")
        self._atomic_write(part_path, data)
        mp.parts[part_number] = MultipartPart(
            part_number=part_number,
            etag=_md5(data),
            size=len(data),
            path=part_path,
        )
        self.kv.set(f"mp:{upload_id}", mp.to_dict())
        return {"part_number": part_number, "etag": _md5(data), "size": len(data)}

    def complete_multipart(self, upload_id: str) -> dict:
        d = self.kv.get(f"mp:{upload_id}")
        if not d:
            raise ValueError(f"unknown upload_id {upload_id}")
        mp = MultipartUpload.from_dict(d)
        if not mp.parts:
            raise ValueError("no parts uploaded")
        # Concat in order
        ordered = sorted(mp.parts.values(), key=lambda p: p.part_number)
        combined = b"".join(open(p.path, "rb").read() for p in ordered)
        # Same PUT path
        result = self.put(mp.bucket, mp.key, combined)
        # Cleanup parts
        for p in ordered:
            try:
                os.remove(p.path)
            except OSError:
                pass
        try:
            os.rmdir(os.path.dirname(ordered[0].path))
        except OSError:
            pass
        self.kv.delete(f"mp:{upload_id}")
        return result

    def abort_multipart(self, upload_id: str) -> bool:
        d = self.kv.get(f"mp:{upload_id}")
        if not d:
            return False
        mp = MultipartUpload.from_dict(d)
        for p in mp.parts.values():
            try:
                os.remove(p.path)
            except OSError:
                pass
        self.kv.delete(f"mp:{upload_id}")
        return True

    def list_multipart(self, upload_id: str) -> Optional[MultipartUpload]:
        d = self.kv.get(f"mp:{upload_id}")
        if not d:
            return None
        return MultipartUpload.from_dict(d)
