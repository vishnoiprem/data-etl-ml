"""User-uploaded documents: extract -> clean -> chunk -> persist -> index.

Storage is one JSON file per collection under APEX_DATA_DIR (atomic
replace, process-local lock). That is right for a single-node deployment up
to tens of thousands of chunks; beyond that, swap this module for the
Qdrant/ES ingest path (same functions, same callers).
"""
from __future__ import annotations

import hashlib
import io
import json
import os
import re
import threading
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

from .textproc import split_sentences
from .sanitize import _INJECTION_RE, redact_pii  # noqa: PLC2701 (same package)
from .settings import get_settings

ALLOWED_EXT = {".txt", ".md", ".csv", ".pdf"}
CHUNK_TARGET = 500   # chars; one chunk == one citable passage
CHUNK_MAX = 800
MAX_PDF_PAGES = 300
_LOCK = threading.Lock()
_STRIP = {"Cc", "Cf", "Co", "Cs"}


class UploadError(ValueError):
    def __init__(self, message: str, status: int = 422):
        super().__init__(message)
        self.status = status


def data_dir() -> Path:
    d = get_settings().data_dir
    p = Path(d) if d else Path(__file__).parent.parent.parent / "data"
    (p / "documents").mkdir(parents=True, exist_ok=True)
    return p


def _path(collection: str) -> Path:
    return data_dir() / "documents" / f"{collection}.json"


def _load(collection: str) -> list[dict]:
    p = _path(collection)
    if not p.exists():
        return []
    try:
        return json.loads(p.read_text())
    except json.JSONDecodeError:
        return []


def _save(collection: str, docs: list[dict]) -> None:
    p = _path(collection)
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(docs, ensure_ascii=False))
    os.replace(tmp, p)  # atomic: readers never see a half-written file


# ---------- extraction / cleaning / chunking ----------

def extract_text(filename: str, data: bytes) -> str:
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXT:
        raise UploadError(f"Unsupported file type '{ext}'. Allowed: {sorted(ALLOWED_EXT)}", 415)
    if ext == ".pdf":
        try:
            from pypdf import PdfReader
        except ImportError as e:  # pragma: no cover
            raise UploadError("PDF support needs `pypdf` (pip install pypdf)", 415) from e
        try:
            reader = PdfReader(io.BytesIO(data))
            if reader.is_encrypted:
                raise UploadError("Encrypted PDFs are not supported")
            return "\n\n".join((pg.extract_text() or "") for pg in reader.pages[:MAX_PDF_PAGES])
        except UploadError:
            raise
        except Exception as e:  # noqa: BLE001
            raise UploadError(f"Could not read PDF: {e.__class__.__name__}") from e
    if b"\x00" in data[:4096]:
        raise UploadError("File looks binary, not text")
    return data.decode("utf-8", errors="replace")


def clean_text(t: str) -> str:
    t = unicodedata.normalize("NFKC", t)
    t = "".join(c for c in t if c in "\n\t" or unicodedata.category(c) not in _STRIP)
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()




def chunk_text(text: str) -> list[str]:
    """Pack paragraphs into ~CHUNK_TARGET-char passages, splitting oversize
    paragraphs on sentence boundaries. Never cuts mid-sentence unless a single
    sentence exceeds CHUNK_MAX."""
    units: list[str] = []
    for para in re.split(r"\n\s*\n", text):
        para = " ".join(para.split())
        if not para:
            continue
        if len(para) <= CHUNK_MAX:
            units.append(para)
            continue
        for s in split_sentences(para):
            while len(s) > CHUNK_MAX:
                units.append(s[:CHUNK_MAX])
                s = s[CHUNK_MAX:]
            if s:
                units.append(s)
    chunks, cur = [], ""
    for u in units:
        if cur and len(cur) + 1 + len(u) > CHUNK_TARGET:
            chunks.append(cur)
            cur = u
        else:
            cur = f"{cur}\n{u}".strip()  # keep paragraph/heading boundaries
    if cur:
        chunks.append(cur)
    return chunks


# ---------- public API ----------

def add_document(collection: str, filename: str, data: bytes) -> dict:
    max_bytes = get_settings().max_upload_bytes
    if len(data) > max_bytes:
        raise UploadError(f"File too large (limit {max_bytes // (1024 * 1024)} MB)", 413)
    text = clean_text(extract_text(filename, data))
    if len(text) < 20:
        raise UploadError("No readable text found in the file")
    digest = hashlib.sha256(text.encode()).hexdigest()
    chunks = chunk_text(text)
    safe_name = re.sub(r"[^\w .()\-]", "_", Path(filename).name)[:120] or "document"
    with _LOCK:
        docs = _load(collection)
        dup = next((d for d in docs if d["sha256"] == digest), None)
        if dup:
            raise UploadError(f"Already uploaded as '{dup['filename']}'", 409)
        rec = {
            "id": digest[:16], "sha256": digest, "filename": safe_name,
            "collection": collection, "chars": len(text), "chunks": chunks,
            "uploaded_at": datetime.now(timezone.utc).isoformat(),
        }
        docs.append(rec)
        _save(collection, docs)
    return {
        "doc_id": rec["id"], "filename": safe_name, "collection": collection,
        "chunks": len(chunks), "chars": len(text),
        "pii_detected": redact_pii(text)[1],
        "injection_like": bool(_INJECTION_RE.search(unicodedata.normalize("NFKC", text))),
    }


def list_documents(collection: str) -> list[dict]:
    return [{k: d[k] for k in ("id", "filename", "chars", "uploaded_at")} | {"chunks": len(d["chunks"])}
            for d in _load(collection)]


def delete_document(collection: str, doc_id: str) -> bool:
    with _LOCK:
        docs = _load(collection)
        keep = [d for d in docs if d["id"] != doc_id]
        if len(keep) == len(docs):
            return False
        _save(collection, keep)
    return True


def passages(collection: str) -> list[tuple[str, str, str]]:
    """(doc_id, title, text) for every uploaded chunk, ready for the index."""
    out = []
    for d in _load(collection):
        n = len(d["chunks"])
        for i, c in enumerate(d["chunks"], 1):
            out.append((f"up-{d['id'][:8]}-{i:03d}", f"{d['filename']} ({i}/{n})", c))
    return out
