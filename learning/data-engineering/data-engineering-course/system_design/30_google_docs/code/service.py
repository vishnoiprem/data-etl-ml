"""Google-Docs-style collaborative document service.

A doc is a string. Each edit is an op: insert(pos, text) or delete(pos, n).
The service keeps the op log, a cached snapshot, and a Lamport-like
version counter. Concurrent ops use a simple "later op wins per line"
strategy.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field, asdict
from typing import Optional

from common.ids import Snowflake
from common.storage import KeyValueStore


@dataclass
class Doc:
    doc_id: int
    title: str
    version: int
    op_count: int
    created_at: float

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Op:
    seq: int
    op: str  # "insert" or "delete"
    pos: int
    text: Optional[str]
    n: int  # delete count
    ts: float
    client_id: Optional[str]
    applied_version: int

    def to_dict(self) -> dict:
        return asdict(self)


class DocsService:
    """Collaborative doc with op log + versioned snapshot.

    >>> svc = DocsService()
    >>> d = svc.create_doc("hello")
    >>> r = svc.apply_op(d.doc_id, op="insert", pos=0, text="Hello world")
    >>> snap = svc.snapshot(d.doc_id)
    >>> snap["content"]
    'Hello world'
    """

    def __init__(self):
        self.snow = Snowflake(machine_id=30)
        self.docs = KeyValueStore("docs_docs")
        self.snaps = KeyValueStore("docs_snaps")
        self.op_log = KeyValueStore("docs_op_log")
        self.doc_ops = KeyValueStore("docs_op_list")
        self.doc_seq = KeyValueStore("docs_seq")
        self._listeners: dict[int, list] = {}

    # ---- lifecycle ---------------------------------------------------

    def create_doc(self, title: str) -> Doc:
        if not isinstance(title, str):
            raise ValueError("title required")
        did = self.snow.next_id()
        d = Doc(
            doc_id=did,
            title=title,
            version=0,
            op_count=0,
            created_at=time.time(),
        )
        self.docs.set(f"doc:{did}", d.to_dict())
        self.snaps.set(f"snap:{did}", {"content": "", "version": 0})
        self.doc_ops.set(f"doc_ops:{did}", [])
        self.doc_seq.set(f"doc_seq:{did}", 0)
        return d

    def get_doc(self, doc_id: int) -> Optional[Doc]:
        d = self.docs.get(f"doc:{doc_id}")
        return Doc(**d) if d else None

    def get_ops(self, doc_id: int) -> list[Op]:
        seqs = self.doc_ops.get(f"doc_ops:{doc_id}") or []
        out: list[Op] = []
        for s in seqs:
            d = self.op_log.get(f"op:{doc_id}:{s}")
            if d:
                out.append(Op(**d))
        return out

    # ---- snapshot -----------------------------------------------------

    def snapshot(self, doc_id: int) -> dict:
        s = self.snaps.get(f"snap:{doc_id}")
        if not s:
            # Cold cache: replay.
            content = self._replay(doc_id)
            doc = self.get_doc(doc_id)
            version = doc.version if doc else 0
            self.snaps.set(f"snap:{doc_id}", {"content": content, "version": version})
            return {"content": content, "version": version}
        return {"content": s["content"], "version": s["version"]}

    def _replay(self, doc_id: int) -> str:
        buf = ""
        for op in self.get_ops(doc_id):
            buf = self._apply_to_string(buf, op)
        return buf

    # ---- apply op -----------------------------------------------------

    def apply_op(
        self,
        doc_id: int,
        op: str,
        pos: int,
        text: Optional[str] = None,
        n: int = 0,
        client_id: Optional[str] = None,
        if_version: Optional[int] = None,
    ) -> dict:
        if op not in ("insert", "delete"):
            raise ValueError("op must be insert|delete")
        doc = self.get_doc(doc_id)
        if not doc:
            raise ValueError("doc not found")
        snap = self.snapshot(doc_id)
        content = snap["content"]
        current_version = snap["version"]

        # Validate position against current length.
        if pos < 0:
            raise ValueError("pos must be >= 0")
        if op == "insert":
            if not isinstance(text, str) or not text:
                raise ValueError("insert requires non-empty text")
            if pos > len(content):
                raise ValueError("pos out of range")
        else:  # delete
            if n <= 0:
                raise ValueError("delete requires n > 0")
            if pos + n > len(content):
                raise ValueError("delete range out of bounds")

        # If if_version doesn't match, apply a simple LWW-per-line rule.
        if if_version is not None and if_version != current_version:
            op = self._line_lww_resolve(content, op, pos, text, n)

        # Apply.
        new_content = self._apply_to_string_with_args(content, op, pos, text, n)
        # Persist.
        new_version = current_version + 1
        new_seq = (self.doc_seq.get(f"doc_seq:{doc_id}") or 0) + 1
        self.doc_seq.set(f"doc_seq:{doc_id}", new_seq)
        self.snaps.set(f"snap:{doc_id}", {"content": new_content, "version": new_version})
        op_record = Op(
            seq=new_seq,
            op=op,
            pos=int(pos),
            text=text,
            n=int(n),
            ts=time.time(),
            client_id=client_id,
            applied_version=current_version,
        )
        self.op_log.set(f"op:{doc_id}:{new_seq}", op_record.to_dict())
        ids = self.doc_ops.get(f"doc_ops:{doc_id}") or []
        ids.append(new_seq)
        self.doc_ops.set(f"doc_ops:{doc_id}", ids)
        doc.version = new_version
        doc.op_count = len(ids)
        self.docs.set(f"doc:{doc_id}", doc.to_dict())

        # Broadcast.
        for q in list(self._listeners.get(doc_id, [])):
            try:
                q.put_nowait({"seq": new_seq, "doc_id": doc_id, "op": op, "pos": pos, "text": text, "n": n, "version": new_version})
            except Exception:
                pass

        return {
            "doc_id": doc_id,
            "seq": new_seq,
            "version": new_version,
            "content": new_content,
        }

    def _line_lww_resolve(
        self,
        content: str,
        op: str,
        pos: int,
        text: Optional[str],
        n: int,
    ):
        # Toy resolution: if there's a concurrent change on the same line,
        # we accept the new op as-is (later op wins).
        # Detect concurrent by checking the line index against the
        # position of the first newline after `pos`. This is intentionally
        # simple — it always returns the op unchanged.
        return op

    # ---- helpers ------------------------------------------------------

    def _apply_to_string(self, content: str, op: Op) -> str:
        return self._apply_to_string_with_args(content, op.op, op.pos, op.text, op.n)

    def _apply_to_string_with_args(
        self,
        content: str,
        op: str,
        pos: int,
        text: Optional[str],
        n: int,
    ) -> str:
        if op == "insert":
            return content[:pos] + (text or "") + content[pos:]
        # delete
        return content[:pos] + content[pos + n:]

    # ---- listeners ----------------------------------------------------

    def register_listener(self, doc_id: int):
        import queue
        q = queue.Queue(maxsize=200)
        self._listeners.setdefault(doc_id, []).append(q)
        return q

    def unregister_listener(self, doc_id: int, q) -> None:
        lst = self._listeners.get(doc_id, [])
        if q in lst:
            lst.remove(q)

    def stats(self) -> dict:
        return {
            "docs": self.docs.size(),
            "ops": self.op_log.size(),
        }
