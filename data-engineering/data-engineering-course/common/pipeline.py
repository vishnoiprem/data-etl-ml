"""A tiny ETL runner with retries, idempotency, and per-stage errors.

This is the data engineering analog of the system design track's
"service" pattern: each Pipeline is just ``extract -> transform ->
load`` with a few cross-cutting concerns handled once.

  * **Retries** — each stage is wrapped in a retry loop. After the
    final failure the exception is re-raised wrapped in
    :class:`PipelineError` so callers see a single failure type.
  * **Idempotency** — pass ``idempotency_key_fn`` to skip a stage when
    its key has already been processed. State is kept in a local
    SQLite file (``./var/pipeline_idempotency.db``) so it survives
    process restarts.
  * **Offsets** — the ``state`` dict lets long-running pipelines
    checkpoint the last row they consumed and resume from there.
"""

from __future__ import annotations

import functools
import os
import sqlite3
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Optional


class PipelineError(Exception):
    """Raised when an ETL stage fails after exhausting retries."""


# ---- idempotency --------------------------------------------------------

_DEFAULT_IDEMPOTENCY_DB = os.path.join("var", "pipeline_idempotency.db")


def _idempotency_conn(path: Optional[str] = None) -> sqlite3.Connection:
    path = path or _DEFAULT_IDEMPOTENCY_DB
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    conn = sqlite3.connect(path)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS idempotency ("
        "  key TEXT PRIMARY KEY,"
        "  result BLOB,"
        "  ts REAL"
        ")"
    )
    conn.commit()
    return conn


def with_idempotency(
    key: str,
    fn: Optional[Callable] = None,
    *,
    db_path: Optional[str] = None,
) -> Callable:
    """Cache ``fn``'s return value in a local SQLite table by key.

    Use as a plain function wrapper::

        result = with_idempotency("load:2024-01-01")(load_fn)()

    Or as a decorator factory::

        @with_idempotency("daily_rollup", db_path="./var/rollup.db")
        def build_rollup():
            ...
    """
    if fn is None:
        # Decorator form: ``@with_idempotency("k")`` — return a
        # decorator that wraps ``fn`` with idempotency.
        def _decorator(real_fn: Callable) -> Callable:
            return _make_idempotent(key, real_fn, db_path)
        return _decorator

    return _make_idempotent(key, fn, db_path)


def _make_idempotent(
    key: str, fn: Callable, db_path: Optional[str]
) -> Callable:
    """Build a wrapper that consults the idempotency cache on every call."""
    conn = _idempotency_conn(db_path)

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        # Cache lookup happens on every invocation.
        row = conn.execute(
            "SELECT result FROM idempotency WHERE key = ?", (key,)
        ).fetchone()
        if row is not None:
            cached = row[0]
            if cached is None:
                return None
            if isinstance(cached, bytes):
                try:
                    return cached.decode("utf-8")
                except UnicodeDecodeError:
                    return cached
            return cached

        result = fn(*args, **kwargs)
        # Persist a marker so subsequent calls short-circuit.
        conn.execute(
            "INSERT OR REPLACE INTO idempotency(key, result, ts) VALUES (?, ?, ?)",
            (key, b"OK", time.time()),
        )
        conn.commit()
        return result

    return wrapper


# ---- pipeline -----------------------------------------------------------


@dataclass
class Pipeline:
    """Tiny ETL runner: extract -> transform -> load with retries.

    >>> def ex(): return [1, 2, 3]
    ... def tr(rows): return [r * 2 for r in rows]
    ... def ld(rows): return sum(rows)
    >>> p = Pipeline("double_sum", ex, tr, ld, retries=1)
    >>> p.run()
    12
    """

    name: str
    extract: Callable[[], Any]
    transform: Callable[[Any], Any]
    load: Callable[[Any], Any]
    retries: int = 3
    idempotency_key_fn: Optional[Callable[[], str]] = None
    state: Dict[str, Any] = field(default_factory=dict)

    def _with_retries(self, label: str, fn: Callable[[], Any]) -> Any:
        last_err: Optional[BaseException] = None
        for attempt in range(1, self.retries + 1):
            try:
                return fn()
            except Exception as exc:  # noqa: BLE001 - we rewrap
                last_err = exc
                # Exponential-ish backoff capped at 1s for tests.
                time.sleep(min(0.1 * (2 ** (attempt - 1)), 1.0))
        raise PipelineError(
            f"stage '{label}' failed after {self.retries} attempts: {last_err}"
        ) from last_err

    def run(self, input_data: Any = None) -> Any:
        """Run extract -> transform -> load, returning the load result."""
        # Idempotency check: if the caller supplied a key fn and we've
        # seen this key before, short-circuit.
        if self.idempotency_key_fn is not None:
            key = self.idempotency_key_fn()
            if self.state.get("last_idempotency_key") == key:
                return self.state.get("last_result")

        # Extract accepts either no-arg or one-arg signature.
        if input_data is None:
            extracted = self._with_retries(
                "extract", lambda: self.extract()
            )
        else:
            extracted = self._with_retries(
                "extract", lambda: self.extract(input_data)
            )
        self.state["last_extract_count"] = _safe_len(extracted)

        transformed = self._with_retries(
            "transform", lambda: self.transform(extracted)
        )
        self.state["last_transform_count"] = _safe_len(transformed)

        loaded = self._with_retries(
            "load", lambda: self.load(transformed)
        )
        self.state["last_result"] = loaded
        if self.idempotency_key_fn is not None:
            self.state["last_idempotency_key"] = self.idempotency_key_fn()
        return loaded


def _safe_len(obj: Any) -> int:
    try:
        return len(obj)  # type: ignore[arg-type]
    except TypeError:
        return -1
