"""Bulk loader: a stand-in for ``COPY INTO parquet_table``.

The real bulk loader in a warehouse is a single ``COPY INTO``
statement. SQLite doesn't have that, so this module simulates
the pattern with bulk ``INSERT`` plus a manifest table for
audit.

The pattern:

  1. Create a staging table with the same schema as the target.
  2. Bulk insert all rows in one ``executemany`` call.
  3. Atomic swap: ``DROP`` target, ``RENAME`` staging → target.
  4. Record the load in the ``load_log`` table.

If the worker crashes between 2 and 3, the staging table is
incomplete and the retry starts over. If it crashes between 3
and 4, the load is complete but the audit log is missing;
a reconciler can detect the discrepancy.

Author: Prem Vishnoi <pvishnoi@avilx.com>
"""

from __future__ import annotations

import time
import uuid
from typing import Any, Dict, Iterable, List, Optional, Sequence

from common import QueryRunner


_LOAD_LOG_DDL = """
CREATE TABLE IF NOT EXISTS load_log (
  load_id     TEXT PRIMARY KEY,
  target      TEXT NOT NULL,
  row_count   INTEGER NOT NULL,
  source      TEXT,
  started_at  REAL NOT NULL,
  finished_at REAL
)
"""


def _ensure_load_log(q: QueryRunner) -> None:
    q.execute(_LOAD_LOG_DDL)


def _coerce_value(v: Any) -> Any:
    if isinstance(v, bool):
        return int(v)
    return v


def bulk_load(
    q: QueryRunner,
    target: str,
    rows: Sequence[Dict[str, Any]],
    *,
    source: Optional[str] = None,
    create_table: bool = True,
) -> Dict[str, Any]:
    """Bulk-load ``rows`` into ``target``.

    Returns a dict with the load_id, row_count, and duration.
    """
    if not rows:
        return {"load_id": None, "row_count": 0, "duration_ms": 0}

    _ensure_load_log(q)
    load_id = str(uuid.uuid4())
    started = time.time()
    q.execute(
        "INSERT INTO load_log (load_id, target, row_count, source, started_at)"
        " VALUES (?, ?, ?, ?, ?)",
        (load_id, target, len(rows), source or "", started),
    )

    # Staging table name uses the load_id; if the load fails, the
    # staging table is left behind and the retry starts over.
    staging = f"{target}__stg_{load_id.replace('-', '_')}"
    columns = list(rows[0].keys())

    if create_table:
        col_defs = []
        for col in columns:
            sample = rows[0][col]
            if isinstance(sample, bool):
                col_defs.append(f'"{col}" INTEGER')
            elif isinstance(sample, int):
                col_defs.append(f'"{col}" INTEGER')
            elif isinstance(sample, float):
                col_defs.append(f'"{col}" REAL')
            else:
                col_defs.append(f'"{col}" TEXT')
        q.execute(
            f'CREATE TABLE "{staging}" ({", ".join(col_defs)})'
        )
    else:
        q.execute(f'CREATE TABLE "{staging}" AS SELECT * FROM "{target}" WHERE 0')

    placeholders = ", ".join("?" for _ in columns)
    cols_csv = ", ".join(f'"{c}"' for c in columns)
    q.executemany(
        f'INSERT INTO "{staging}" ({cols_csv}) VALUES ({placeholders})',
        [tuple(_coerce_value(r.get(c)) for c in columns) for r in rows],
    )

    # Atomic swap.
    q.execute(f'DROP TABLE IF EXISTS "{target}"')
    q.execute(f'ALTER TABLE "{staging}" RENAME TO "{target}"')

    finished = time.time()
    duration_ms = int((finished - started) * 1000)
    q.execute(
        "UPDATE load_log SET finished_at = ? WHERE load_id = ?",
        (finished, load_id),
    )
    return {
        "load_id": load_id,
        "row_count": len(rows),
        "duration_ms": duration_ms,
    }


def get_load_history(
    q: QueryRunner, target: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Return the load history, optionally filtered by target."""
    _ensure_load_log(q)
    if target:
        return q.query_all(
            "SELECT * FROM load_log WHERE target = ? ORDER BY started_at DESC",
            (target,),
        )
    return q.query_all("SELECT * FROM load_log ORDER BY started_at DESC")
