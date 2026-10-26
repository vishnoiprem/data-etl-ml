"""SQLite query runner with parameter binding and result helpers.

This is the data engineering analog of the ``KeyValueStore`` used in
the system design track. It exists so every track can talk to SQLite
the same way — point reads, point writes, batched writes, and a
context manager that closes the connection deterministically.
"""

from __future__ import annotations

import sqlite3
from typing import Any, Iterator, List, Optional, Sequence


class QueryRunner:
    """A small wrapper over :mod:`sqlite3` with dict-style results.

    >>> with QueryRunner(":memory:") as q:
    ...     q.execute("CREATE TABLE t (id INTEGER PRIMARY KEY, n INTEGER)")
    ...     q.executemany("INSERT INTO t(n) VALUES (?)", [(1,), (2,), (3,)])
    ...     q.query_all("SELECT n FROM t ORDER BY n")
    [{'n': 1}, {'n': 2}, {'n': 3}]
    """

    def __init__(self, db_path: str = ":memory:"):
        self.db_path = db_path
        # `detect_types` lets sqlite3 adapt a few common types
        # automatically; we mostly pass primitives anyway.
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row

    # ---- core operations ------------------------------------------------

    def execute(self, sql: str, params: Sequence[Any] = ()) -> int:
        """Execute a single statement, return rowcount."""
        cur = self.conn.execute(sql, params)
        self.conn.commit()
        return cur.rowcount

    def executemany(
        self, sql: str, seq_of_params: Sequence[Sequence[Any]]
    ) -> int:
        """Batch execute a parameterized statement, return total rowcount."""
        cur = self.conn.executemany(sql, seq_of_params)
        self.conn.commit()
        return cur.rowcount

    def query_all(
        self, sql: str, params: Sequence[Any] = ()
    ) -> List[dict]:
        """Return all rows as a list of dicts."""
        cur = self.conn.execute(sql, params)
        return [dict(row) for row in cur.fetchall()]

    def query_one(
        self, sql: str, params: Sequence[Any] = ()
    ) -> Optional[dict]:
        """Return the first row as a dict, or ``None`` if no row matches."""
        cur = self.conn.execute(sql, params)
        row = cur.fetchone()
        return dict(row) if row is not None else None

    def query_iter(
        self, sql: str, params: Sequence[Any] = ()
    ) -> Iterator[dict]:
        """Stream rows one at a time — useful for large result sets."""
        cur = self.conn.execute(sql, params)
        for row in cur:
            yield dict(row)

    # ---- lifecycle ------------------------------------------------------

    def close(self) -> None:
        """Close the underlying connection."""
        self.conn.close()

    def __enter__(self) -> "QueryRunner":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()
