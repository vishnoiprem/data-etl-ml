"""User-data export pipeline — core service.

The flow is:

    POST /api/exports    -> enqueue
    worker tick          -> QUEUED -> RUNNING -> READY
    GET /api/exports/<id>/download -> blob bytes
    expiry sweep         -> READY -> EXPIRED (and blob deleted)

User data is gathered from a set of pluggable ``Collection``
objects. The export itself is a single JSON document persisted
under ``var/blobs/{export_id}.json``.

This module is HTTP-free; ``app.py`` is the Flask wrapper.
"""

from __future__ import annotations

import json
import os
import threading
import time
from collections import deque
from dataclasses import dataclass, field, asdict
from typing import Any, Callable, Deque, Dict, List, Optional

from common.ids import Snowflake
from common.storage import KeyValueStore


# ----------------------------- defaults -----------------------------------

DEFAULT_TTL_SECONDS = 24 * 3600
DEFAULT_MAX_BLOB_BYTES = 10 * 1024 * 1024     # 10 MB
DEFAULT_WORKER_IDLE_SLEEP = 0.05
DEFAULT_BLOB_DIR = "var/blobs"


# ----------------------------- exceptions ---------------------------------


class ExportError(Exception):
    pass


class ExportNotFoundError(ExportError):
    pass


class InvalidUserError(ExportError):
    pass


# ----------------------------- collections --------------------------------


class Collection:
    """A pluggable reader for one slice of user data."""

    name: str = "collection"

    def collect(self, user_id: str) -> List[Dict[str, Any]]:
        raise NotImplementedError


class UserProfileCollection(Collection):
    name = "profile"

    def __init__(self, profiles: Optional[Dict[str, Dict[str, Any]]] = None):
        self.profiles = profiles or {}

    def collect(self, user_id: str) -> List[Dict[str, Any]]:
        p = self.profiles.get(user_id)
        return [p] if p else []


class OrdersCollection(Collection):
    name = "orders"

    def __init__(self, orders: Optional[Dict[str, List[Dict[str, Any]]]] = None):
        self.orders = orders or {}

    def collect(self, user_id: str) -> List[Dict[str, Any]]:
        return list(self.orders.get(user_id, []))


class ActivityCollection(Collection):
    name = "activity"

    def __init__(self, activity: Optional[Dict[str, List[Dict[str, Any]]]] = None):
        self.activity = activity or {}

    def collect(self, user_id: str) -> List[Dict[str, Any]]:
        return list(self.activity.get(user_id, []))


class PreferencesCollection(Collection):
    name = "preferences"

    def __init__(self, prefs: Optional[Dict[str, Dict[str, Any]]] = None):
        self.prefs = prefs or {}

    def collect(self, user_id: str) -> List[Dict[str, Any]]:
        p = self.prefs.get(user_id)
        return [p] if p else []


# ----------------------------- dataclass ----------------------------------


@dataclass
class Export:
    export_id: int
    user_id: str
    status: str = "queued"   # queued | running | ready | failed | expired
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    finished_at: Optional[float] = None
    expires_at: Optional[float] = None
    size_bytes: int = 0
    collections: List[str] = field(default_factory=list)
    error: Optional[str] = None
    blob_filename: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)


# ----------------------------- blob store ---------------------------------


class BlobStore:
    """Tiny file-backed blob store.

    Each export has a single file under ``root`` named after the
    export id. We use ``.json`` for the demo; in production this
    would be S3 / GCS with a signed URL.
    """

    def __init__(self, root: str = DEFAULT_BLOB_DIR):
        self.root = root
        os.makedirs(self.root, exist_ok=True)

    def path(self, export_id: int) -> str:
        return os.path.join(self.root, f"{export_id}.json")

    def write(self, export_id: int, payload: Dict[str, Any]) -> int:
        path = self.path(export_id)
        tmp = f"{path}.{int(time.time() * 1000)}.tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, sort_keys=True)
        os.replace(tmp, path)
        return os.path.getsize(path)

    def read(self, export_id: int) -> Optional[Dict[str, Any]]:
        path = self.path(export_id)
        if not os.path.exists(path):
            return None
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def exists(self, export_id: int) -> bool:
        return os.path.exists(self.path(export_id))

    def delete(self, export_id: int) -> bool:
        path = self.path(export_id)
        if os.path.exists(path):
            os.remove(path)
            return True
        return False


# ----------------------------- the service --------------------------------


class ExportService:
    """Async user-data export pipeline.

    >>> s = ExportService(start_worker=False)
    >>> e = s.create_export("u-1")
    >>> s.run_once()
    >>> s.get_export(e.export_id)["status"] in ("ready", "running")
    True
    """

    def __init__(
        self,
        store: Optional[KeyValueStore] = None,
        blob_store: Optional[BlobStore] = None,
        idgen: Optional[Snowflake] = None,
        collections: Optional[List[Collection]] = None,
        ttl_seconds: float = DEFAULT_TTL_SECONDS,
        max_blob_bytes: int = DEFAULT_MAX_BLOB_BYTES,
        time_fn: Callable[[], float] = time.time,
        start_worker: bool = True,
    ):
        self.store = store or KeyValueStore("user_data_export")
        self.blob_store = blob_store or BlobStore()
        self.idgen = idgen or Snowflake(machine_id=12)
        self.collections: List[Collection] = list(
            collections
            or [
                UserProfileCollection(),
                OrdersCollection(),
                ActivityCollection(),
                PreferencesCollection(),
            ]
        )
        self.ttl_seconds = ttl_seconds
        self.max_blob_bytes = max_blob_bytes
        self.time_fn = time_fn

        # In-process queue of export ids in dispatch order.
        self._queue: Deque[int] = deque()
        self._wake = threading.Event()
        self._stop = threading.Event()
        self._worker: Optional[threading.Thread] = None
        self._lock = threading.RLock()

        # Recover: any RUNNING exports go back to QUEUED.
        self._recover_in_flight()
        if start_worker:
            self.start_worker()

    # ---- lifecycle ------------------------------------------------------

    def start_worker(self) -> None:
        with self._lock:
            if self._worker and self._worker.is_alive():
                return
            self._stop.clear()
            self._recover_in_flight()
            self._seed_queue_from_store()
            self._worker = threading.Thread(
                target=self._worker_loop,
                name="export-worker",
                daemon=True,
            )
            self._worker.start()

    def stop_worker(self, timeout: float = 1.0) -> None:
        with self._lock:
            self._stop.set()
            self._wake.set()
        if self._worker:
            self._worker.join(timeout=timeout)

    def _worker_loop(self) -> None:
        while not self._stop.is_set():
            try:
                progressed = self.run_once()
            except Exception:  # pragma: no cover
                progressed = False
            if not progressed:
                self._wake.wait(timeout=DEFAULT_WORKER_IDLE_SLEEP)
                self._wake.clear()

    def _recover_in_flight(self) -> None:
        for k, v in list(self.store.scan("export:")):
            if v.get("status") in ("running",):
                v["status"] = "queued"
                v["started_at"] = None
                self.store.set(k, v)
                exp_id = int(v["export_id"])
                if exp_id not in self._queue:
                    self._queue.append(exp_id)

    def _seed_queue_from_store(self) -> None:
        for k, v in self.store.scan("export:"):
            if v.get("status") == "queued":
                exp_id = int(v["export_id"])
                if exp_id not in self._queue:
                    self._queue.append(exp_id)

    # ---- write path -----------------------------------------------------

    def create_export(self, user_id: str) -> Export:
        if not isinstance(user_id, str) or not user_id.strip():
            raise InvalidUserError("user_id must be a non-empty string")
        user_id = user_id.strip()
        export = Export(
            export_id=self.idgen.next_id(),
            user_id=user_id,
            created_at=self.time_fn(),
            collections=[c.name for c in self.collections],
        )
        self._persist(export)
        with self._lock:
            self._queue.append(export.export_id)
        self._wake.set()
        return export

    def _persist(self, export: Export) -> None:
        self.store.set(f"export:{export.export_id}", export.to_dict())
        idx = self.store.get("exportindex:all", [])
        if export.export_id not in idx:
            idx.append(export.export_id)
            self.store.set("exportindex:all", idx)
        uk = f"exportindex:user:{export.user_id}"
        ulist = self.store.get(uk, [])
        if export.export_id not in ulist:
            ulist.append(export.export_id)
            self.store.set(uk, ulist)

    # ---- worker tick ----------------------------------------------------

    def run_once(self) -> bool:
        """Do one unit of work: expiry sweep + one export attempt."""
        self._expire_due()
        with self._lock:
            if not self._queue:
                return False
            export_id = self._queue[0]
        data = self.store.get(f"export:{export_id}")
        if not data:
            with self._lock:
                if self._queue and self._queue[0] == export_id:
                    self._queue.popleft()
            return True
        if data.get("status") != "queued":
            with self._lock:
                if self._queue and self._queue[0] == export_id:
                    self._queue.popleft()
            return True

        # RUNNING.
        data["status"] = "running"
        data["started_at"] = self.time_fn()
        self.store.set(f"export:{export_id}", data)

        try:
            payload = self._compile(data["user_id"])
        except Exception as e:
            with self._lock:
                if self._queue and self._queue[0] == export_id:
                    self._queue.popleft()
            data["status"] = "failed"
            data["error"] = f"{type(e).__name__}: {e}"
            data["finished_at"] = self.time_fn()
            self.store.set(f"export:{export_id}", data)
            return True

        # Size guard.
        encoded = json.dumps(payload)
        size = len(encoded.encode("utf-8"))
        if size > self.max_blob_bytes:
            with self._lock:
                if self._queue and self._queue[0] == export_id:
                    self._queue.popleft()
            data["status"] = "failed"
            data["error"] = f"export too large: {size} > {self.max_blob_bytes}"
            data["finished_at"] = self.time_fn()
            self.store.set(f"export:{export_id}", data)
            return True

        try:
            self.blob_store.write(export_id, payload)
        except OSError as e:
            with self._lock:
                if self._queue and self._queue[0] == export_id:
                    self._queue.popleft()
            data["status"] = "failed"
            data["error"] = f"blob write failed: {e}"
            data["finished_at"] = self.time_fn()
            self.store.set(f"export:{export_id}", data)
            return True

        with self._lock:
            if self._queue and self._queue[0] == export_id:
                self._queue.popleft()
        data["status"] = "ready"
        data["finished_at"] = self.time_fn()
        data["expires_at"] = self.time_fn() + self.ttl_seconds
        data["size_bytes"] = size
        data["blob_filename"] = self.blob_store.path(export_id)
        self.store.set(f"export:{export_id}", data)
        return True

    def _compile(self, user_id: str) -> Dict[str, Any]:
        sections: Dict[str, Any] = {}
        for coll in self.collections:
            sections[coll.name] = coll.collect(user_id)
        return {
            "meta": {
                "user_id": user_id,
                "generated_at": self.time_fn(),
                "format": "json",
                "version": 1,
            },
            "data": sections,
        }

    # ---- expiry ---------------------------------------------------------

    def _expire_due(self) -> None:
        now = self.time_fn()
        for k, v in list(self.store.scan("export:")):
            if v.get("status") == "ready":
                exp = v.get("expires_at")
                if exp is not None and exp <= now:
                    v["status"] = "expired"
                    self.store.set(k, v)
                    try:
                        self.blob_store.delete(int(v["export_id"]))
                    except OSError:
                        pass

    # ---- read paths -----------------------------------------------------

    def get_export(self, export_id: int) -> Dict[str, Any]:
        data = self.store.get(f"export:{export_id}")
        if not data:
            raise ExportNotFoundError(str(export_id))
        return data

    def list_exports(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        if user_id is not None:
            ids = self.store.get(f"exportindex:user:{user_id}", [])
        else:
            ids = self.store.get("exportindex:all", [])
        out = []
        for eid in ids:
            d = self.store.get(f"export:{eid}")
            if d:
                out.append(d)
        out.sort(key=lambda d: d.get("created_at", 0), reverse=True)
        return out

    def download(self, export_id: int) -> Dict[str, Any]:
        data = self.get_export(export_id)
        status = data.get("status")
        if status == "expired":
            raise ExportNotFoundError(f"export {export_id} expired")
        if status != "ready":
            raise ExportError(f"export {export_id} not ready: {status}")
        # Honour lazy expiry.
        exp = data.get("expires_at")
        if exp is not None and exp <= self.time_fn():
            data["status"] = "expired"
            self.store.set(f"export:{export_id}", data)
            try:
                self.blob_store.delete(export_id)
            except OSError:
                pass
            raise ExportNotFoundError(f"export {export_id} expired")
        blob = self.blob_store.read(export_id)
        if blob is None:
            raise ExportError(f"export {export_id} blob missing")
        return blob

    # ---- inspection helpers -------------------------------------------

    def status(self) -> dict:
        counts = {"queued": 0, "running": 0, "ready": 0, "failed": 0, "expired": 0}
        for _k, v in self.store.scan("export:"):
            counts[v.get("status", "unknown")] = counts.get(v.get("status", "unknown"), 0) + 1
        with self._lock:
            return {
                "queue_size": len(self._queue),
                "counts": counts,
                "total": sum(counts.values()),
                "ttl_seconds": self.ttl_seconds,
                "max_blob_bytes": self.max_blob_bytes,
                "collections": [c.name for c in self.collections],
            }
