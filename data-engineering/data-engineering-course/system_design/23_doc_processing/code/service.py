"""Document processing pipeline service.

State machine:
    UPLOADED -> PARSED -> EXTRACTED -> INDEXED
                            (or FAILED)

A background worker thread drives the state forward. The HTTP layer is a
thin control plane over `DocumentService`.
"""

from __future__ import annotations

import re
import threading
import time
from typing import Callable, Optional

from common.ids import Snowflake
from common.storage import KeyValueStore

UPLOADED = "UPLOADED"
PARSED = "PARSED"
EXTRACTED = "EXTRACTED"
INDEXED = "INDEXED"
FAILED = "FAILED"
TERMINAL = {INDEXED, FAILED}

WORKER_TICK_S = 0.05  # 50ms — fast for tests
INVERTED_MAX_PER_TOKEN = 1_000
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
MONEY_RE = re.compile(r"\$\s?\d[\d,]*\.?\d*")
PHONE_RE = re.compile(r"\+?\d[\d\-\s]{7,}\d")


def _now_ms() -> int:
    return int(time.time() * 1000)


def _tokenize(text: str) -> list[str]:
    return [t.lower() for t in re.findall(r"[A-Za-z0-9_]+", text) if t]


# ----------------------------------------------------------------------
# default stage functions
# ----------------------------------------------------------------------


def default_parse(doc: dict) -> str:
    """In the real world this would OCR the doc. Here we just normalize."""
    return (doc.get("content") or "").strip()


def default_extract(parsed_text: str) -> list[dict]:
    """Pull a few canned entity types via regex."""
    if not parsed_text:
        return []
    entities: list[dict] = []
    for m in EMAIL_RE.findall(parsed_text):
        entities.append({"type": "email", "value": m})
    for m in MONEY_RE.findall(parsed_text):
        entities.append({"type": "money", "value": m})
    for m in PHONE_RE.findall(parsed_text):
        entities.append({"type": "phone", "value": m.strip()})
    # Fallback: harvest capitalized words as "org" candidates.
    for m in re.findall(r"\b[A-Z][a-zA-Z]{2,}\b", parsed_text):
        entities.append({"type": "org", "value": m})
    return entities


def default_index(doc: dict) -> None:
    """The act of indexing is just stamping a timestamp; the inverted
    index is built when the service transitions to INDEXED."""
    doc["indexed_at_ms"] = _now_ms()


# ----------------------------------------------------------------------
# service
# ----------------------------------------------------------------------


class DocumentService:
    """Coordinates upload, state transitions, and search."""

    def __init__(
        self,
        store: Optional[KeyValueStore] = None,
        snowflake: Optional[Snowflake] = None,
        start_worker: bool = True,
    ):
        self.store = store or KeyValueStore("docproc", persist_path=None)
        self.id_gen = snowflake or Snowflake(machine_id=3)
        self._lock = threading.RLock()
        self._worker_stop = threading.Event()
        self._worker: Optional[threading.Thread] = None
        if start_worker:
            self._start_worker()

    # ---- worker -------------------------------------------------------

    def _start_worker(self) -> None:
        if self._worker and self._worker.is_alive():
            return
        self._worker_stop.clear()
        t = threading.Thread(target=self._run_worker, daemon=True,
                             name="docproc-worker")
        t.start()
        self._worker = t

    def stop_worker(self) -> None:
        self._worker_stop.set()

    def worker_alive(self) -> bool:
        return self._worker is not None and self._worker.is_alive()

    def _run_worker(self) -> None:
        while not self._worker_stop.is_set():
            try:
                self._tick()
            except Exception:
                # Don't let a single bad doc kill the worker.
                pass
            self._worker_stop.wait(WORKER_TICK_S)

    def _tick(self) -> None:
        # Find the first non-terminal doc.
        with self._lock:
            for did in self.store.get("docs:index") or []:
                rec = self.store.get(f"doc:{did}")
                if not rec:
                    continue
                if rec.get("status") in TERMINAL:
                    continue
                self._advance(rec)
                return

    def _advance(self, doc: dict) -> None:
        status = doc.get("status")
        if status == UPLOADED:
            doc["parsed_text"] = default_parse(doc)
            doc["status"] = PARSED
        elif status == PARSED:
            doc["entities"] = default_extract(doc.get("parsed_text", ""))
            doc["status"] = EXTRACTED
        elif status == EXTRACTED:
            default_index(doc)
            doc["status"] = INDEXED
            self._add_to_inverted_index(doc)
        else:
            return
        self.store.set(f"doc:{doc['id']}", doc)

    def _add_to_inverted_index(self, doc: dict) -> None:
        text = doc.get("parsed_text", "") + " " + " ".join(
            e.get("value", "") for e in doc.get("entities", [])
        )
        for tok in set(_tokenize(text)):
            key = f"search:term:{tok}"
            ids = list(self.store.get(key) or [])
            if doc["id"] not in ids:
                ids.append(doc["id"])
                if len(ids) > INVERTED_MAX_PER_TOKEN:
                    ids = ids[-INVERTED_MAX_PER_TOKEN:]
                self.store.set(key, ids)

    # ---- public API ---------------------------------------------------

    def upload(self, content: str, doc_type: str = "text") -> dict:
        if content is None:
            raise ValueError("content required")
        did = str(self.id_gen.next_id())
        now = _now_ms()
        rec = {
            "id": did,
            "type": doc_type,
            "content": content,
            "status": UPLOADED,
            "uploaded_at_ms": now,
            "parsed_text": "",
            "entities": [],
        }
        self.store.set(f"doc:{did}", rec)
        with self._lock:
            idx = list(self.store.get("docs:index") or [])
            idx.append(did)
            self.store.set("docs:index", idx)
        return rec

    def get(self, doc_id: str) -> Optional[dict]:
        return self.store.get(f"doc:{doc_id}")

    def entities(self, doc_id: str) -> list[dict]:
        rec = self.store.get(f"doc:{doc_id}")
        if not rec:
            return []
        return rec.get("entities") or []

    def search(self, q: str, limit: int = 25) -> list[dict]:
        tokens = _tokenize(q)
        if not tokens:
            return []
        candidate_ids: Optional[set[str]] = None
        for tok in tokens:
            ids = set(self.store.get(f"search:term:{tok}") or [])
            candidate_ids = ids if candidate_ids is None else (
                candidate_ids & ids
            )
            if not candidate_ids:
                return []
        out: list[dict] = []
        for did in candidate_ids or []:
            rec = self.store.get(f"doc:{did}")
            if not rec or rec.get("status") != INDEXED:
                continue
            haystack = (
                rec.get("parsed_text", "")
                + " "
                + " ".join(e.get("value", "") for e in rec.get("entities", []))
            )
            if any(tok in haystack.lower() for tok in tokens):
                out.append({
                    "id": rec["id"],
                    "snippet": rec.get("parsed_text", "")[:200],
                    "entities": rec.get("entities", []),
                })
                if len(out) >= limit:
                    break
        return out

    # ---- test helpers -------------------------------------------------

    def force_advance_all(self) -> None:
        """Synchronously advance every doc to INDEXED. For tests only."""
        with self._lock:
            for did in list(self.store.get("docs:index") or []):
                rec = self.store.get(f"doc:{did}")
                if not rec:
                    continue
                while rec.get("status") not in TERMINAL:
                    self._advance(rec)
                    rec = self.store.get(f"doc:{did}")
                    if rec is None:
                        break

    def stats(self) -> dict:
        return {
            "docs": len(self.store.get("docs:index") or []),
            "worker_alive": self.worker_alive(),
        }
